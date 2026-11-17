SELECT 'CREATE DATABASE webshop_analytics'  
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'webshop_analytics')\gexec
