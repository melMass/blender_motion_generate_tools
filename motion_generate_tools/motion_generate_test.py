import logging
import os

import torch
from torch.utils import data

from mdm.data_loaders import tensors
from mdm.data_loaders.humanml.data.dataset import HumanML3D
from mdm.data_loaders.humanml.scripts import motion_process
from mdm.data_loaders.humanml.utils import paramUtil
from mdm.data_loaders.tensors import t2m_collate
from mdm.model import cfg_sampler
from mdm.utils import dist_util, fixseed, model_util
from motion_utils import DATA_PATH, config_logging, disable_tqdm_globally, dotdict

SMPL_DATA_PATH = os.path.join(DATA_PATH, 'body_models', 'smpl')
SMPL_MODEL_PATH = os.path.join(SMPL_DATA_PATH, 'SMPL_NEUTRAL.pkl')
JOINT_REGRESSOR_TRAIN_EXTRA_PATH = os.path.join(SMPL_DATA_PATH, 'J_regressor_extra.npy')
MODEL_PATH = os.path.join(DATA_PATH, 'save', 'humanml_trans_enc_512', 'model000200000.pt')


def main():
    config_logging()
    disable_tqdm_globally()

    seed = 1
    motion_length = 2.0  # secs
    max_frames = 196
    fps = 30
    n_frames = min(max_frames, int(motion_length * fps))
    guidance_param = 2.5
    device = 0
    text_prompt = "a person jumps"
    num_repetitions = 1
    batch_size = 1
    dataset = 'humanml'

    fixseed.fixseed(seed)

    dist_util.setup_dist(device)

    data_loader = data.DataLoader(
        HumanML3D(mode='text_only', base_path=DATA_PATH, split='test', num_frames=max_frames),
        batch_size=batch_size, shuffle=True,
        num_workers=8, drop_last=True, collate_fn=t2m_collate
    )

    model = model_util.MDM(
        smpl_model_path=SMPL_MODEL_PATH,
        joint_regressor_train_extra_path=JOINT_REGRESSOR_TRAIN_EXTRA_PATH,
        **model_util.get_model_args(dotdict({
            'dataset': dataset,
            'smpl_data_path': os.path.join(DATA_PATH, 'body_models/smpl'),
            'latent_dim': 512,
            'layers': 8,
            'cond_mask_prob': 0.1,
            'arch': 'trans_enc',
            'emb_trans_dec': False,
        }), data_loader)
    )

    diffusion = model_util.create_gaussian_diffusion(dotdict({
        'noise_schedule': 'cosine',
        'sigma_small': True,
        'lambda_vel': 0.0,
        'lambda_rcxyz': 0.0,
        'lambda_fc': 0.0,
    }))

    state_dict = torch.load(MODEL_PATH, map_location='cpu')
    model_util.load_model_wo_clip(model, state_dict)

    model = cfg_sampler.ClassifierFreeSampleModel(model)
    model.to(dist_util.dev())
    model.eval()  # disable random masking

    _, model_kwargs = tensors.collate([{
        'inp': torch.tensor([[0.]]),
        'target': 0,
        'text': text_prompt,
        'tokens': None,
        'lengths': n_frames
    }])

    all_text = []
    all_motions = []
    all_lengths = []

    for rep_i in range(num_repetitions):
        logging.info(f'### Start sampling [repetitions #{rep_i}]')

        model_kwargs['y']['scale'] = torch.ones(batch_size, device=dist_util.dev()) * guidance_param

        sample = diffusion.p_sample_loop(
            model,
            (batch_size, model.njoints, model.nfeats, n_frames),
            clip_denoised=False,
            model_kwargs=model_kwargs,
            skip_timesteps=0,  # 0 is the default value - i.e. don't skip any step
            init_image=None,
            progress=True,
            dump_steps=None,
            noise=None,
            const_noise=False,
        )

        # Recover XYZ *positions* from HumanML3D vector representation
        if model.data_rep == 'hml_vec':
            n_joints = 22 if sample.shape[1] == 263 else 21
            sample = data_loader.dataset.t2m_dataset.inv_transform(sample.cpu().permute(0, 2, 3, 1)).float()
            sample = motion_process.recover_from_ric(sample, n_joints)
            sample = sample.view(-1, *sample.shape[2:]).permute(0, 2, 3, 1)

        all_text += model_kwargs['y']['text']
        all_motions.append(sample.cpu().numpy())
        all_lengths.append(model_kwargs['y']['lengths'].cpu().numpy())

        logging.info(f"created {len(all_motions) * batch_size} samples")

    skeleton = paramUtil.t2m_kinematic_chain


if __name__ == '__main__':
    main()
