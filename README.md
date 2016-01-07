[![Build Status](https://travis-ci.org/zalando/solrcloud-cli.svg?branch=master)](https://travis-ci.org/zalando/solrcloud-cli?branch=master)
[![Coverage Status](https://coveralls.io/repos/zalando/solrcloud-cli/badge.svg?branch=master&service=github)](https://coveralls.io/github/zalando/solrcloud-cli?branch=master)

# SolrCloud-CLI

Deployment tool for [STUPS](https://stups.io/) SolrCloud appliance.

## Table of contents
1. Install SolrCloud-CLI
2. Bootstrapping Solr cloud
3. Blue/green deployment of new Solr cloud version
4. Delete complete cluster

## 1 Install SolrCloud-CLI

        $ sudo python3 setup.py install
        
## 2 Bootstrap Solr cloud

        $ mai login
        $ pierone login
        $ solrcloud -s 3 -r 3 -b https://example.org/solr -i 1.0.x -f example.yaml <application id> bootstrap


## 3 Blue/green deployment of new Solr cloud version

### 3.1 Solr cloud deployment in one step

        $ mai login
        $ pierone login
        $ solrcloud -b https://example.org/solr -i 1.0.x -f example.yaml <application id> deploy

### 3.2 Solr cloud deployment in single steps
1. Authorization for deployment

        $ mai login
        $ pierone login

2. Create new stack version
        
        $ solrcloud -b https://example.org/solr -i 1.0.x -f example.yaml <application id> create-new-cluster

3. Add new nodes to cluster
        
        $ solrcloud -b https://example.org/solr -i 1.0.x -f example.yaml <application id> add-new-nodes

4. Switch traffic to new nodes
        
        $ solrcloud -b https://example.org/solr -i 1.0.x -f example.yaml <application id> switch

5. Delete old nodes in cluster
        
        $ solrcloud -b https://example.org/solr -i 1.0.x -f example.yaml <application id> delete-old-nodes

6. Terminate old stack version
        
        $ solrcloud -b https://example.org/solr -i 1.0.x -f example.yaml <application id> delete-old-cluster

## 4 Delete complete cluster

        $ mai login
        $ pierone login
        $ solrcloud -b https://example.org/solr -f example.yaml <application id> delete
