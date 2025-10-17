-- Neutralize delivery carrier
UPDATE delivery_carrier
SET username = 'test',
    password = 'test',
    access_token = ''
WHERE delivery_type = 'viettelpost';
