#!/usr/bin/env python
# -*- encoding: utf-8 -*

import torch.nn as nn
import math
from ..core.base_ops import h_sigmoid, h_swish, conv_1x1_bn, conv_3x3_bn, _make_divisible, InvertedResidual


class MobileNet(nn.Module):
    def __init__(
        self,
        dep_mul,
        wid_mul,
        out_features=("dark3", "dark4", "dark5"),
    ):
        super(MobileNet, self).__init__()
        # setting of inverted residual blocks

        base_channels = _make_divisible(16 * wid_mul, 8)

        # stem
        self.stem  = conv_3x3_bn(3, 16, 2)

        # stage 1 [in, hidden, out, k, s, se, hs]
        self.stage1 = nn.Sequential(
                InvertedResidual(16, 16, 16, 3, 1, False, False),
                InvertedResidual(16, 64, 24, 3, 2, False, False),
                InvertedResidual(24, 72, 24, 3, 1, False, False),
        )

        # stage 2
        self.stage2 = nn.Sequential(
                InvertedResidual(24, 72, 40, 5, 2, True, False),
                InvertedResidual(40, 120, 40, 5, 1, True, False),
                InvertedResidual(40, 120, 40, 5, 1, True, False),
        )

        # stage 3
        self.stage3 = nn.Sequential(
                InvertedResidual(40, 240, 80, 3, 2, False, True),
                InvertedResidual(80, 200, 80, 3, 1, False, True),
                InvertedResidual(80, 184, 80, 3, 1, False, True),
                InvertedResidual(80, 184, 80, 3, 1, False, True),

                InvertedResidual(80, 480, 112, 3, 1, True, True),
                InvertedResidual(112, 672, 112, 3, 1, True, True),
                InvertedResidual(112, 672, 160, 5, 1, True, True),
        )

        # stage 4
        self.stage4 = nn.Sequential(
                InvertedResidual(160, 672, 160, 5, 2, True, True),
                InvertedResidual(160, 960, 160, 5, 1, True, True),
        )       


    def init_weights(self, pretrain=None):

        if pretrain is None:
            return
        else:
            pretrained_dict = torch.load(pretrain, map_location='cpu')['state_dict']
            new_params = self.state_dict().copy()
            for k, v in pretrained_dict.items():
                ks = k.split('.')
                if ks[0] == 'fc' or ks[-1] == 'total_ops' or ks[-1] == 'total_params':
                    continue
                else:
                    new_params[k] = v

            self.load_state_dict(new_params)
            print(f" load pretrain backbone from {pretrain}")


    def forward(self, x):
        outputs = {}
        x = self.stem(x)
        outputs["stem"] = x
        x = self.stage1(x)
        outputs["stage1"] = x
        x = self.stage2(x)
        outputs["stage2"] = x
        x = self.stage3(x)
        outputs["stage3"] = x
        x = self.stage4(x)
        outputs["stage4"] = x
        features_out = [outputs["stem"], outputs["stage1"], outputs["stage2"], outputs["stage3"], outputs["stage4"]]

        return features_out