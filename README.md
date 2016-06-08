[![Build Status](https://travis-ci.org/zalando-incubator/solrcloud-cli.svg?branch=master)](https://travis-ci.org/zalando-incubator/solrcloud-cli?branch=master)
[![Coverage Status](https://codecov.io/github/zalando-incubator/solrcloud-cli/coverage.svg?branch=master)](https://codecov.io/github/zalando-incubator/solrcloud-cli?branch=master)

# SolrCloud-CLI

Deployment tool for [STUPS](https://stups.io/) [SolrCloud appliance](https://github.com/zalando/solrcloud-appliance).

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
        $ solrcloud -s 3 -r 3 -i 1.0.x -f example.yaml bootstrap


## 3 Blue/green deployment of new Solr cloud version

### 3.1 Solr cloud deployment in one step

        $ mai login
        $ pierone login
        $ solrcloud -i 1.0.x -f example.yaml deploy

### 3.2 Solr cloud deployment in single steps
1. Authorization for deployment

        $ mai login
        $ pierone login

2. Create new stack version
        
        $ solrcloud -i 1.0.x -f example.yaml create-new-cluster

3. Add new nodes to cluster
        
        $ solrcloud -i 1.0.x -f example.yaml add-new-nodes

4. Switch traffic to new nodes
        
        $ solrcloud -i 1.0.x -f example.yaml switch

5. Delete old nodes in cluster
        
        $ solrcloud -i 1.0.x -f example.yaml delete-old-nodes

6. Terminate old stack version
        
        $ solrcloud -i 1.0.x -f example.yaml delete-old-cluster

## 4 Delete complete cluster

        $ mai login
        $ pierone login
        $ solrcloud -f example.yaml delete
