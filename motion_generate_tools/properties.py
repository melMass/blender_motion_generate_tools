# -*- coding: utf-8 -*-
# Copyright 2022 UuuNyaa <UuuNyaa@gmail.com>
# This file is part of Motion Generate Tools.

import bpy


class MotionGeneratorToolsProperties(bpy.types.PropertyGroup):
    text_condition: bpy.props.StringProperty(name='Text Condition')
    diffusion_sampling_steps: bpy.props.IntProperty(name='Diffusion Sampling Steps', default=100, min=1, soft_max=200, max=1000)
    seed: bpy.props.IntProperty(name='Seed', default=0, min=0, max=1000000)
    guidance_param: bpy.props.FloatProperty(name='Guidance Param', default=2.5, min=0.0, max=10.0)
    text_samples: bpy.props.IntProperty(name='Text Samples', default=1, min=1, max=100)
    batch_size: bpy.props.IntProperty(name='Batch Size', default=1, min=1, max=100)
    diffusion_steps: bpy.props.IntProperty(name='Diffusion Steps', default=1000, min=1, max=100000)
    
    @staticmethod
    def register():
        # pylint: disable=assignment-from-no-return
        bpy.types.WindowManager.motion_generator_tools = bpy.props.PointerProperty(type=MotionGeneratorToolsProperties)

    @staticmethod
    def unregister():
        del bpy.types.WindowManager.motion_generator_tools
