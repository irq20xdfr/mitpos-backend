# Docker Image Build Instructions

This README provides instructions on how to build and run the Docker image for this project.

## Prerequisites

- Docker installed on your system. You can download and install Docker from [here](https://www.docker.com/get-started).

## Building the Docker Image

To build the Docker image, follow these steps:

1. Open a terminal and navigate to the project directory containing the Dockerfile.

2. Run the following command to build the image:

   ```
   docker build -t mitpos .
   ```

   This command builds a Docker image with the tag `mitpos` using the Dockerfile in the current directory.

## Running the Docker Container

After building the image, you can run the container using the following command:
