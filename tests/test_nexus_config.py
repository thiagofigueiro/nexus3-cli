# -*- coding: utf-8 -*-
from nexuscli.nexus_config import NexusConfig


def test_write_config(config_args):
    """Ensure values written in config file can be read back"""
    nexus_config = NexusConfig(**config_args)
    nexus_config.dump()

    nexus_loaded_config = NexusConfig(config_path=config_args['config_path'])
    assert nexus_config.to_dict != nexus_loaded_config.to_dict

    nexus_loaded_config.load()
    assert nexus_config.to_dict == nexus_loaded_config.to_dict
