def _try_get_user_funboost_common_config(funboost_common_conf_field:str):
    try:
        import funboost_config  # This file may not exist before first startup, or configuration may be needed before initialization.
        return getattr(funboost_config.FunboostCommonConfig,funboost_common_conf_field)
    except Exception as e:
        # print(e)
        return None