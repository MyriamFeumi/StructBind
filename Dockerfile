FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    git \
    make \
    gcc \
    g++ \
    libnetcdf-dev \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/Discngine/fpocket.git /tmp/fpocket \
    && cd /tmp/fpocket \
    && sed -i 's/CFLAGS = /CFLAGS = -Wno-error=incompatible-pointer-types /' makefile \
    && make \
    && make install \
    && rm -rf /tmp/fpocket

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]