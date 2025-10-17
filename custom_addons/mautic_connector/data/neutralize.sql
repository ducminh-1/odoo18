-- Remove mautic credentials
UPDATE ir_config_parameter
SET value = 'test'
WHERE key in ('mautic_api_user', 'mautic_api_password');
