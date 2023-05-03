def link_files [] {
    [
        data_loaders/humanml/common/quaternion.py
        data_loaders/humanml/common/skeleton.py
        data_loaders/humanml/scripts/motion_process.py
        data_loaders/humanml/utils/paramUtil.py
        data_loaders/tensors.py
        diffusion/gaussian_diffusion.py
        diffusion/losses.py
        diffusion/nn.py
        diffusion/respace.py
        model/cfg_sampler.py
        model/mdm.py
        model/rotation2xyz.py
        model/smpl.py
        utils/config.py
        utils/dist_util.py
        utils/fixseed.py
        utils/model_util.py
        utils/rotation_conversions.py
    ]
}



def main [] {
    let src_dir = ($env.FILE_PWD | path join "mdm")
    let target_dir = ($env.FILE_PWD | path join "motion_generate_tools" "mdm")

    mkdir $target_dir

    link_files | each { |f|
        let file = if $nu.os-info.name == "windows" {
            ($f | str replace -a '/' '\')
        } else {
            $f
        }
        let src_file = ($src_dir | path join $file)
        let target_file = ($target_dir | path join $file)
        # {
        #     target_exist: ($target_file | path exists)
        #     src_exist: ($src_file | path exists)

        # }
        mkdir ($target_file | path dirname)
        cp $src_file $target_file
    }
}