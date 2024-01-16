
# Rate Limiter

This project implements various rate-limiting algorithms in Python using asyncio, semaphore techniques. The rate limiters include:

- Sliding Window Counter Limiter
- Sliding Window Log Limiter
- Fixed Window Counter Limiter (User Level)
- Fixed Window Counter Limiter (Server Level)
- Token Bucket Rate Limiter

### Sliding Window Counter Limiter:

**Use Case:**
- Used to limit the number of requests within a specified time window.

**Pros:**
- Simple and easy to implement.
- Efficient for scenarios where the rate limit can be fixed per window.

**Cons:**
- May not handle burst requests well if the window size is small.
- Can be affected by clock skew if not implemented carefully.

### Sliding Window Log Limiter:

**Use Case:**
- Designed to limit requests based on a logarithmic function of the recent request times.

**Pros:**
- More flexibility in adjusting to varying request patterns.
- Can handle burst requests better than a simple counter.

**Cons:**
- More complex to implement compared to a simple sliding window counter.
- May have higher memory overhead due to log storage.

### Fixed Window Counter Limiter (User Level):

**Use Case:**
- Limits the number of requests for a user within a fixed time window.

**Pros:**
- Effective for controlling the rate at which a single user can make requests.
- Provides isolation between users.

**Cons:**
- May not be suitable for scenarios where the rate limit needs to be shared among all users.

### Fixed Window Counter Limiter (Server Level):

**Use Case:**
- Similar to user-level fixed window counter but applied at the server level for all users.

**Pros:**
- Ensures fairness among all users by applying the same rate limit to everyone.
- Effective for global rate limiting.

**Cons:**
- May not provide sufficient isolation between users.

### Token Bucket Rate Limiter:

**Use Case:**
- Controls the rate of requests by using a token-based system where tokens are replenished over time.

**Pros:**
- Handles burst requests effectively.
- Provides a smoother rate limiting mechanism.

**Cons:**
- More complex to implement.
- Requires managing tokens and a refill strategy.

### Comparison:

- **Sliding Window Counter vs. Sliding Window Log Limiter:**
  - Counter is simpler, while Log Limiter provides more flexibility.

- **Fixed Window Counter (User Level) vs. Fixed Window Counter (Server Level):**
  - User Level is suitable for user-specific rate limiting, while Server Level is more global.

- **Sliding Window Counter vs. Token Bucket Rate Limiter:**
  - Token Bucket is more versatile and handles burst requests better.

Each algorithm has its strengths and weaknesses, and the choice depends on the specific requirements of the application and the desired behavior of rate limiting.


## Installation

### Conda based

Before running the application, make sure to install the required dependencies. The project uses Conda for managing dependencies, and you can set up the environment using the provided `environment.yml` file.

```bash
conda env create -f environment.yml
```

Activate the Conda environment:

```bash
conda activate your_environment_name
```

Usage
The main module contains the implementation of rate-limiting algorithms. You can customize and extend these implementations based on your requirements.

Running the Application
To run the application, execute the `main.py` script:

```bash
python main/main.py -limiteralgo algorithm_type
```
Replace algorithm_type with one of the following options:
```
swc: Sliding Window Counter
swl: Sliding Window Log
fwcsl: Fixed Window Counter (Server Level)
fwcul: Fixed Window Counter (User Level)
tbl: Token Bucket Limiter
```
Testing
The test directory contains unit tests for the implemented rate limiters. You can run the tests using pytest. Ensure your Conda environment is activated before running the tests:
```bash
pytest ratelimitertest.py
```

### Docker based
Run the application in Docker with conda by:
```bash
docker build -f Dockerfile-Conda .
```
or plain python
```bash
docker build -f Dockerfile .
```
You can pass your algorithms when running the docker command.

```bash
docker run -p 8080:8080 your_image_name -limiteralgo your_algorithm_type
```



