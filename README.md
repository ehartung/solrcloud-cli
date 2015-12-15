[![Build Status](https://travis-ci.org/zalando/solrcloud-cli.svg)](https://travis-ci.org/zalando/solrcloud-cli)

# SolrCloud-CLI

Deployment tool for [STUPS](https://stups.io/) SolrCloud appliance.

## Table of contents
1. Bootstrapping Solr cloud
2. Blue/green deployment of new Solr cloud version
3. Delete complete cluster

## 1 Bootstrap Solr cloud

        $ mai login
        $ TOKEN=$(zign token uid)
        $ ./solrcloud-cli -s 3 -r 3 -t $TOKEN -b https://example.org/solr -i 1.0.x <application id> bootstrap


## 2 Blue/green deployment of new Solr cloud version

### 2.1 Solr cloud deployment in one step

        $ pierone login
        $ mai login
        $ TOKEN=$(zign token uid)
        $ ./solrcloud-cli -t $TOKEN -b https://example.org/solr -i 1.0.x <application id> deploy

### 2.2 Solr cloud deployment in single step
1. Authorization for deployment

        $ mai login
        $ TOKEN=$(zign token uid)

2. Create new stack version
        
        $ ./solrcloud-cli -t $TOKEN -b https://example.org/solr -i 1.0.x <application id> create-new-cluster

3. Add new nodes to cluster
        
        $ ./solrcloud-cli -t $TOKEN -b https://example.org/solr -i 1.0.x <application id> add-new-nodes

4. Switch traffic to new nodes
        
        $ ./solrcloud-cli -t $TOKEN -b https://example.org/solr -i 1.0.x <application id> switch

5. Delete old nodes in cluster
        
        $ ./solrcloud-cli -t $TOKEN -b https://example.org/solr -i 1.0.x <application id> delete-old-nodes

6. Terminate old stack version
        
        $ ./solrcloud-cli -t $TOKEN -b https://example.org/solr -i 1.0.x <application id> delete-old-cluster

## 3 Delete complete cluster

        $ mai login
        $ pierone login
        $ TOKEN=$(zign token uid)
        $ ./solrcloud-cli -t $TOKEN -b https://example.org/solr <application id> delete
