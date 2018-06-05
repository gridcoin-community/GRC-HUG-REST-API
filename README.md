# Gridcoin HUG REST API

The purpose of this Gridcoin HUG REST API repo is to provide an open-source high performance interface to the Gridcoin network through simple GET requests.

By following the readme, you can easily recreate the API in your own control. Do remember to change the API key and rpc details you've configured in the gridcoinresearch.conf file.

## License

The contents of this entire repo should be considered MIT licenced.

## How to contribute

It's difficult to debug development issues whilst running behind Gunicorn & NGINX, you're best running the HUG REST API directly with HUG during development "hug -f hug.py". Note that running HUG directly in this manner should only be performed during development, it is not suitable for exposing directly to the public as a production ready API.

### About: HUG

> ##### Embrace the APIs of the future
> Drastically simplify API development over multiple interfaces. With hug, design and develop your API once, then expose it however your clients need to consume it. Be it locally, over HTTP, or through the command line - hug is the fastest and most modern way to create APIs on Python3.
> ##### Unparalleled performance
> hug has been built from the ground up with performance in mind. It is built to consume resources only when necessary and is then compiled with Cython to achieve amazing performance. As a result, hug consistently benchmarks as one of the fastest Python frameworks and without question takes the crown as the fastest high-level framework for Python 3.
>
> Source: [Official website](http://www.hug.rest/).

---

## Install guide

This is an install guide for Ubuntu 17.10. The HUG REST API uses Python3, HUG, Gunicorn & NGINX. If you change the OS or server components then the following guide will be less applicable, if you succeed please do provide a separate readme for alternative implementation solutions.

### Setup dependencies & Python environment

We create the 'grcapi' user, however you could rename this to whatever you want, just remember to change the NGINX & Gunicorn configuration files.

#### Setup a dedicated user

    adduser grcapi
    <ENTER NEW PASSWORD>
    <CONFIRM NEW PASSWORD>
    usermod -aG sudo grcapi
    sudo usermod -a -G www-data grcapi
    su - grcapi

#### Install required applications

    sudo apt-get install libffi-dev libssl-dev python3-pip python3-dev build-essential git nginx python3-setuptools virtualenv libcurl4-openssl-dev

#### Create Python virtual environment

    mkdir HUG
    virtualenv -p python3 HUG
    echo "source ./HUG/bin/activate" > access_env.sh
    chmod +x access_env.sh
    source access_env.sh

#### Install Python packages

    pip3 install --upgrade pip
    pip3 install --upgrade setuptools
    pip3 install --upgrade wheel
    pip3 install requests
    pip3 install hug
    pip3 install gunicorn
    pip3 install json

### Configure NGINX

NGINX serves as a reverse web proxy to Gunicorn & uses an UNIX socket instead of an IP address for referencing Gunicorn.

    Copy the nginx.conf file to /etc/nginx/
    Reset nginx (sudo service nginx restart)

    sudo mv default /etc/nginx/sites-available/default

### Implement SSL Cert

You aught to implement a free LetsEncrypt SSL certificate, this requires a domain name (they don't sign IP addresses) and it needs to be renewed every few months by running certbot again. NOTE: Replace ```api.domain.tld``` with your own full domain path.

https://certbot.eff.org/

    sudo add-apt-repository ppa:certbot/certbot
    sudo apt-get update
    sudo apt-get install python-certbot-nginx
    sudo certbot --nginx -d api.domain.tld

### Configure Gunicorn

Official website: http://gunicorn.org/

Documentation: http://docs.gunicorn.org/en/stable/

Gunicorn is used to provide scalable worker process management and task buffering for the HUG REST API. Gunicorn's documentation states that each CPU can provide roughly 2-3+ Gunicorn workers, however it may be able to achieve a higher quantity (worth testing).

    cp gunicorn.service /etc/systemd/system/gunicorn.service
    sudo systemctl start gunicorn
    sudo systemctl enable gunicorn

### MISC

If you make changes to the service or the hug script:

    sudo systemctl daemon-reload
    sudo systemctl restart gunicorn

If you want to monitor Gunicorn:

    tail -f gunicorn_access_log
    tail -f gunicorn_error_log
    sudo systemctl status gunicorn

---

# Available HUG REST API functionality

This section will detail the functionality which will be available to the public through GET requests.

The functions are currently all read-only functions, enabling the public to request data from the network without the risk of exposing critical wallet controls.

## Mining

Mining commands.

### function

function description

##### Parameters

* example_parameter `string`
* api_key `string`

##### Usage
`https://subdomain.domain.tld/function?example_parameter=12345&api_key=123abc`

#### [Run: Production command]()
#### [Run: Testnet command]()

## Network

Network command.

## Wallet

Wallet commands.
