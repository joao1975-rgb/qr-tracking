def detect_device_info(user_agent_string: str) -> Dict[str, str]:
    """Detectar información del dispositivo desde User-Agent"""
    try:
        user_agent = user_agents.parse(user_agent_string)
        if user_agent.is_mobile:
            device_type = 'Mobile'
        elif user_agent.is_tablet:
            device_type = 'Tablet'
        elif user_agent.is_pc:
            device_type = 'Desktop'
        else:
            device_type = 'Unknown'
        return {'device_type': device_type, 'browser': f'{user_agent.browser.family} {user_agent.browser.version_string}', 'operating_system': f'{user_agent.os.family} {user_agent.os.version_string}', 'is_mobile': user_agent.is_mobile, 'is_tablet': user_agent.is_tablet, 'is_pc': user_agent.is_pc, 'brand': user_agent.device.brand or 'Unknown', 'model': user_agent.device.model or 'Unknown'}
    except Exception as e:
        logger.warning(f'Error detectando dispositivo: {e}')
        return {'device_type': 'Unknown', 'browser': 'Unknown', 'operating_system': 'Unknown', 'is_mobile': False, 'is_tablet': False, 'is_pc': False, 'brand': 'Unknown', 'model': 'Unknown'}