# MC - Document to Image Processing Service

It is a Python-based document processing service that converts various document formats (PDF, DOCX, PPT, Excel) to images and extracts information using Vision-Language Models (VLM).

## Features

- Convert various document formats to images:
  - PDF files
  - Microsoft Word documents (.doc, .docx)
  - Microsoft PowerPoint presentations (.ppt, .pptx)
  - Microsoft Excel spreadsheets (.xlsx)
- Extract information from documents using Vision-Language Models
- RESTful API built with FastAPI
- Docker containerization for easy deployment
- Support for Chinese characters

## Prerequisites

- Docker
- Docker Compose

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd mc
   ```

2. Build and start the service using Docker Compose:
   ```bash
   docker-compose up -d
   ```

The service will be available at `http://localhost:9040`.

## Usage

### API Endpoints

1. **Root Endpoint**
   ```
   GET /
   ```
   Returns basic API information.

2. **Health Check**
   ```
   GET /api/health
   ```
   Returns the health status of the service.

3. **Document Processing**
   ```
   POST /parse_file
   ```
   Upload a document file to convert it to images and extract information.

   Example using curl:
   ```bash
   curl -X POST "http://localhost:9040/parse_file" \
        -H "accept: application/json" \
        -H "Content-Type: multipart/form-data" \
        -F "file=@path/to/your/document.pdf"
   ```

### Supported File Types

- PDF (.pdf)
- Word Documents (.doc, .docx)
- PowerPoint Presentations (.ppt, .pptx)
- Excel Spreadsheets (.xlsx)

## Configuration

The service can be configured using environment variables:

| Variable | Description | Default Value |
|----------|-------------|---------------|
| `API_HOST` | Host address for the API | `0.0.0.0` |
| `API_PORT` | Port for the API | `8000` |
| `API_RELOAD` | Enable auto-reload | `True` |
| `MODEL_URL` | URL for the VLM API | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| `API_KEY` | API key for the VLM service | `sk-68763db8f6254eefa4c61fa0d0d131a1` |
| `VLM_MODEL` | VLM model to use | `qwen-vl-max-latest` |
| `IMAGES_SAVE_DIR` | Directory to save images | `data/images` |

## Technical Architecture

The service is built using the following technologies:

- **FastAPI**: Web framework for building the API
- **LibreOffice**: Converts Office documents to PDF
- **Poppler**: Converts PDF files to images
- **Vision-Language Model (VLM)**: Extracts information from images
- **Docker**: Containerization for consistent deployment

### Data Flow

1. User uploads a document file
2. If the file is not already a PDF, LibreOffice converts it to PDF
3. Poppler converts the PDF to images
4. Images are sent to the VLM for information extraction
5. Results are returned in JSON format

## Dependencies

- fastapi==0.116.1
- uvicorn[standard]==0.24.0
- pandas==2.1.3
- openpyxl==3.1.2
- pdf2image~=1.17.0
- openai==1.88.0
- python-multipart==0.0.9
- fuzzywuzzy==0.18.0
- python-levenshtein==0.23.0
- pydantic==2.11.7

## Development

To run the service locally for development:

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Install system dependencies:
   ```bash
   sudo apt install libreoffice poppler-utils
   ```

3. Install Chinese fonts to prevent character encoding issues:
   ```bash
   sudo apt install xfonts-utils
   sudo mkfontscale
   sudo mkfontdir
   sudo fc-cache -fv
   ```

4. Run the application:
   ```bash
   python main.py
   ```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Thanks to the FastAPI team for providing an excellent framework
- Thanks to the LibreOffice and Poppler communities for document processing tools
- Thanks to Alibaba DashScope for providing the VLM API