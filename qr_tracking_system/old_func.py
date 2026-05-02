def detect_device_info(user_agent_string: str, client_hint_model: str=None) -> Dict[str, str]:
    """Detectar información del dispositivo usando device-detector con soporte ClientHints"""
    try:
        import re
        from device_detector import DeviceDetector
        if client_hint_model and 'Android' in user_agent_string:
            user_agent_string = re.sub('(Android [^;]+;)\\s*[^)]+', f'\\1 {client_hint_model}', user_agent_string)
            scans_logger.info(f'ClientHints Inyectado -> {client_hint_model}')
        device = DeviceDetector(user_agent_string).parse()
        dtype = device.device_type()
        is_mobile = dtype in ['smartphone', 'feature phone', 'phablet']
        is_tablet = dtype == 'tablet'
        is_pc = dtype == 'desktop'
        device_type = 'smartphone' if is_mobile else 'tablet' if is_tablet else 'desktop' if is_pc else 'Unknown'
        device_brand = device.device_brand() if device.device_brand() else 'Unknown'
        device_model = device.device_model() if device.device_model() else 'Unknown'
        os_info = f'{device.os_name()} {device.os_version()}'.strip()
        browser_info = f'{device.client_name()} {device.client_version()}'.strip()
        return {'device_type': device_type, 'device_brand': device_brand, 'device_model': device_model, 'browser': browser_info if browser_info else 'Unknown', 'operating_system': os_info if os_info else 'Unknown', 'is_mobile': is_mobile, 'is_tablet': is_tablet, 'is_pc': is_pc}
    except Exception as e:
        logger.warning(f'Error detectando dispositivo: {e}')
        return {'device_type': 'Unknown', 'device_brand': 'Unknown', 'device_model': 'Unknown', 'browser': 'Unknown', 'operating_system': 'Unknown', 'is_mobile': False, 'is_tablet': False, 'is_pc': False}