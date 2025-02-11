# luna-v0
Distillation at its finest

# Start servers

./paroli-server --encoder encoder.onnx --decoder decoder.rknn -c config.json --ip 0.0.0.0 --port 8848
ollama serve
ollama run luna:latest --verbose

