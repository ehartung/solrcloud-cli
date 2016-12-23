[![Build Status](https://travis-ci.org/zalando-incubator/solrcloud-cli.svg?branch=master)](https://travis-ci.org/zalando-incubator/solrcloud-cli?branch=master)
[![Coverage Status](https://codecov.io/github/zalando-incubator/solrcloud-cli/coverage.svg?branch=master)](https://codecov.io/github/zalando-incubator/solrcloud-cli?branch=master)

# SolrCloud-CLI

Deployment tool for [STUPS](https://stups.io/) [SolrCloud appliance](https://github.com/zalando/solrcloud-appliance).

## Table of contents
1. Install SolrCloud-CLI
2. Supported deployment methods
3. Bootstrapping Solr cloud
4. Blue/green deployment of new Solr cloud version
5. Delete complete cluster

## 1 Install SolrCloud-CLI

        $ sudo python3 setup.py install
        
## 2 Supported deployment methods

### 2.1 STUPS (default)

Authorization steps:

        $ mai login
        $ pierone login

### 2.2 Kubernetes (K8s)

Authorization steps:

        $ zkubectl login kube.example.org 
        $ pierone login
        
## 3 Bootstrap SolrCloud

        $ solrcloud -s 3 -r 3 -i 1.0.x -f example.yaml bootstrap


## 4 Blue/green deployment of new SolrCloud version

### 4.1 Solr cloud deployment in one step

        $ solrcloud -i 1.0.x -f example.yaml deploy

### 4.2 SolrCloud deployment in single steps
1. Create new stack version
        
        $ solrcloud -i 1.0.x -f example.yaml create-new-cluster

2. Add new nodes to cluster
        
        $ solrcloud -i 1.0.x -f example.yaml add-new-nodes

3. Switch traffic to new nodes
        
        $ solrcloud -i 1.0.x -f example.yaml switch

4. Delete old nodes in cluster
        
        $ solrcloud -i 1.0.x -f example.yaml delete-old-nodes

5. Terminate old stack version
        
        $ solrcloud -i 1.0.x -f example.yaml delete-old-cluster

## 5 Delete complete cluster

        $ solrcloud -f example.yaml delete
