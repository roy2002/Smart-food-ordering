#!/bin/bash
# Generate gRPC Python code from proto files

python -m grpc_tools.protoc \
    -I./proto \
    --python_out=. \
    --grpc_python_out=. \
    ./proto/order.proto

echo "gRPC code generated successfully!"
