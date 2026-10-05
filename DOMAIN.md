# Pointing a domain here

jackgreer.com is taken (registered 2012, in use by another Jack Greer).
Available as of Oct 2026: jackgreer.co, jackgreer.me, jackgreer.photo,
jgreerfilm.com, greerjack.com

Once you own one:

1. Create a file named `CNAME` in this repo containing just the domain,
   no protocol, no trailing slash. Example contents: jackgreer.co
2. At the registrar, set DNS:

   Apex (jackgreer.co), four A records:
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

3. GitHub repo Settings > Pages > Custom domain, enter the domain, Save.
4. Wait for the DNS check to pass, then tick Enforce HTTPS.

Also update these in index.html: the og:url, og:image and canonical tags
currently say jackgreer.co.
