# Custom domain: greerjack.com

Registered at Porkbun. The `CNAME` file in this repo holds the domain.

DNS at Porkbun (Domain Management > greerjack.com > DNS). Delete Porkbun's
default parking records first (the ALIAS/CNAME pointing at pixie.porkbun.com).

  Apex (host blank), four A records:
    185.199.108.153
    185.199.109.153
    185.199.110.153
    185.199.111.153

  Apex, four AAAA records:
    2606:50c0:8000::153
    2606:50c0:8001::153
    2606:50c0:8002::153
    2606:50c0:8003::153

  www subdomain, one CNAME record:
    www  ->  jxgreer1.github.io

Then GitHub repo Settings > Pages > Custom domain: greerjack.com, Save.
Wait for the DNS check to pass, then tick Enforce HTTPS.
