host=${1:-dms}
size=${2:-5000}

curl -s -XGET ${host}:9200/volvo-z1-raw-v1/_search?size=${size}\&pretty -d '
{
  "query": { 
      "match": {"cluster_id": "islp00001"}
  }
}'
