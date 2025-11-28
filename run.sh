set -e  # Exit on any error

# Define image and container names
IMAGE_NAME="finalcase_2025"
CONTAINER_NAME="finalcase_2025_container"

# Load environment variables
if [ -f .env ]; then
    ENV_FILE=".env"
elif [ -f .env.example ]; then
    echo ".env not found, using .env.example"
    ENV_FILE=".env.example"
else
    echo "No .env or .env.example found, using defaults from code"
    ENV_FILE=""
fi

if [ -n "$ENV_FILE" ]; then
    export $(grep -v '^#' $ENV_FILE | xargs)
fi

# Use PORT from env, default to 5000
HOST_PORT=${PORT:-5000}

# Build the Docker image
echo "Building Docker image..."
docker build -t $IMAGE_NAME .

# Stop and remove any existing container
if [ "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
    echo "Stopping and removing existing container..."
    docker stop $CONTAINER_NAME
    docker rm $CONTAINER_NAME
fi

# Run the container
echo "Running container on port $HOST_PORT..."
docker run -d \
    --name $CONTAINER_NAME \
    $( [ -n "$ENV_FILE" ] && echo "--env-file $ENV_FILE" ) \
    -p $HOST_PORT:$HOST_PORT \
    $IMAGE_NAME

echo "App is running on http://localhost:$HOST_PORT"
