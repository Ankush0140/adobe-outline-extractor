# Adobe India Hackathon - Round 1A

## How to Run

Build:
```bash
docker build -t pdf-processor .


docker run --rm -v "%cd%/input:/app/input:ro" -v "%cd%/output:/app/output" --network none pdf-processor
