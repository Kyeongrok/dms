# ELK Stack in Docker
Run the ELK (Elasticseach, Logstash, Kibana) stack with Docker and Docker-compose, based on the official images:
* [elasticsearch](https://registry.hub.docker.com/_/elasticsearch/)
* [logstash](https://registry.hub.docker.com/_/logstash/)
* [kibana](https://registry.hub.docker.com/_/kibana/)

# Setup
1. Install [Docker](http://docker.io).
2. Install [Docker-compose](http://docs.docker.com/compose/install/)
3. Clone this repository

# Quick Start
Start the ELK stack with *docker-compose*:
```bash
$ cd elastic-docker
$ docker-compose up -d
```

Access Kibana UI [http://<docker_box>:5601](http://<docker_box>:5601) with a web browser. Note that you will need to select an index pattern first, e.g., **metricbeat-***. Then click **Dashboard** and open an sample dashboard by clicking **Open** button on the top right area.

# Configurations
Configurations are in their respective directories. Adjust *docker-compose.yml" and other configurations files as needed.
