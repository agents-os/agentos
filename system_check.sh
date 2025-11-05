-e #!/bin/bash

echo "Disk Usage:"
df -h

echo "Memory Usage:"
free -h

echo "Running Processes:"
ps aux
