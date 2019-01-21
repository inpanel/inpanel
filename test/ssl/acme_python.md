1. 创建一个 Let's Encrypt API 账户私钥, 以便让其识别你的身份 Create a Let's Encrypt account private key (if you haven't already)

    ```shell
    openssl genrsa 4096 > account.key
    ```

2. 创建域名证书请求文件(CSR) Create a certificate signing request (CSR) for your domains.

    ```shell
    # 生成域名私钥 Generate a domain private key (if you haven't already)
    openssl genrsa 4096 > github.com.key
    ```

    创建请求文件

    ```shell
    # 单个域名 For a single domain
    openssl req -new -sha256 -key github.com.key -subj "/CN=github.com" > github.com.csr
    # 多个域名 For multiple domains (use this one if you want both www.github.com and github.com)
    openssl req -new -sha256 -key github.com.key -subj "/" -reqexts SAN -config <(cat /etc/ssh/ssh_config <(printf "[SAN]\nsubjectAltName=DNS:github.com,DNS:www.github.com,DNS:test.github.com")) > github.com.csr
    ```

3. 配置验证域名所有权的服务,创建验证目录

    ```shell
    mkdir -p /var/www/challenges/
    ```

4. 配置一个 HTTP 服务让 LETSENCRYPT 能下载验证文件

    ```shell
    server {
        listen 80;
        server_name github.com www.github.com;

        location /.well-known/acme-challenge/ {
            alias /var/www/challenges/;
            try_files $uri =404;
        }
    ...the rest of your config
    }
    ```

5. 获取签名证书 Get a signed certificate

    ```shell
    # Run the script on your server
    python acme_tiny.py --account-key ./account.key --csr ./github.com.csr --acme-dir /var/www/challenges/ > ./github.com.signed.crt
    ```

6. 转化 crt 到 pem 文件

    ```shell
    wget -O - https://letsencrypt.org/certs/lets-encrypt-x3-cross-signed.pem > intermediate.pem
    cat github.com.signed.crt intermediate.pem > github.com.pem
    ```

7. 配置 nginx 主机

    ```
    server {
        listen 443 ssl;
        server_name github.com;
        ssl_certificate         /etc/nginx/ssl/github.com.pem;
        ssl_certificate_key     /etc/nginx/ssl/github.com.key;
        ssl_session_cache       shared:SSL:1m;
        ssl_session_timeout     5m;
        location / {
            proxy_pass http://127.0.0.1:8080/;
            proxy_redirect off;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }
    }
    ```

8. 脚本覆盖策略

    基于此证书 3 个月有效期，此外建立一个脚本进行一个证书覆盖操作。(所以此方法建议测试环境验证 https 环境，并不建议应用到生产环境)

    ```shell
    vi ~/letsencrypt/renew_cert.sh
    #!/usr/bin/sh
    python /path/to/acme_tiny.py --account-key /path/to/account.key --csr /path/to/domain.csr --acme-dir /var/www/challenges/ > /tmp/signed.crt || exit
    wget -O - https://letsencrypt.org/certs/lets-encrypt-x3-cross-signed.pem > intermediate.pem
    cat /tmp/signed.crt intermediate.pem > /path/to/github.com.pem
    service nginx reload
    chmod +x renew_cert.sh
    ```

9. 加入 crontab

    ```shell
    0 0 1 \* \* ~/letsencrypt/renew_cert.sh 2>> /var/log/acme_tiny.log
    ```

