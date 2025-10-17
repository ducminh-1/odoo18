-- Neutralize Vihat
UPDATE ir_config_parameter
SET value = 'test'
WHERE key in ('vihat_api_key', 'vihat_secret_key');
