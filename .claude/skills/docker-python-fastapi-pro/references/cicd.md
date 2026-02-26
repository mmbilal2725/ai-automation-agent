# CI/CD Integration for Docker Python/FastAPI

Comprehensive guide to integrating Docker builds into CI/CD pipelines with examples for GitHub Actions, GitLab CI, and Jenkins.

## GitHub Actions

### Basic Build and Push

```yaml
name: Docker Build and Push

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3

    - name: Log in to Container Registry
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=semver,pattern={{version}}
          type=semver,pattern={{major}}.{{minor}}
          type=sha,prefix={{branch}}-

    - name: Build and push Docker image
      uses: docker/build-push-action@v5
      with:
        context: .
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=registry,ref=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:buildcache
        cache-to: type=registry,ref=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:buildcache,mode=max
```

### Build with Tests and Security Scanning

```yaml
name: Docker CI/CD Pipeline

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.13'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Run tests
      run: |
        pytest --cov=. --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3

    - name: Build Docker image
      uses: docker/build-push-action@v5
      with:
        context: .
        load: true
        tags: app:${{ github.sha }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: app:${{ github.sha }}
        format: 'sarif'
        output: 'trivy-results.sarif'
        severity: 'CRITICAL,HIGH'

    - name: Upload Trivy results to GitHub Security
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: 'trivy-results.sarif'

    - name: Test Docker image
      run: |
        docker run -d --name test-container -p 8000:8000 app:${{ github.sha }}
        sleep 10
        curl -f http://localhost:8000/health || exit 1
        docker logs test-container
        docker stop test-container

    - name: Log in to Registry
      uses: docker/login-action@v3
      with:
        registry: ghcr.io
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    - name: Push Docker image
      run: |
        docker tag app:${{ github.sha }} ghcr.io/${{ github.repository }}:latest
        docker tag app:${{ github.sha }} ghcr.io/${{ github.repository }}:${{ github.sha }}
        docker push ghcr.io/${{ github.repository }}:latest
        docker push ghcr.io/${{ github.repository }}:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
    - name: Deploy to Kubernetes
      run: |
        echo "Deploy to K8s"
        # kubectl set image deployment/app app=ghcr.io/${{ github.repository }}:${{ github.sha }}
```

### Multi-Platform Build

```yaml
name: Multi-Platform Docker Build

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4

    - name: Set up QEMU
      uses: docker/setup-qemu-action@v3

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3

    - name: Log in to Registry
      uses: docker/login-action@v3
      with:
        registry: ghcr.io
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    - name: Build and push multi-platform
      uses: docker/build-push-action@v5
      with:
        context: .
        platforms: linux/amd64,linux/arm64
        push: true
        tags: |
          ghcr.io/${{ github.repository }}:latest
          ghcr.io/${{ github.repository }}:${{ github.ref_name }}
        cache-from: type=gha
        cache-to: type=gha,mode=max
```

## GitLab CI

### Basic Pipeline

```yaml
# .gitlab-ci.yml

stages:
  - test
  - build
  - deploy

variables:
  DOCKER_DRIVER: overlay2
  DOCKER_TLS_CERTDIR: "/certs"
  IMAGE_TAG: $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  LATEST_TAG: $CI_REGISTRY_IMAGE:latest

# Run tests
test:
  stage: test
  image: python:3.13-slim
  before_script:
    - pip install --upgrade pip
    - pip install -r requirements.txt
    - pip install -r requirements-dev.txt
  script:
    - pytest --cov=. --cov-report=term --cov-report=xml
  coverage: '/TOTAL.*\s+(\d+%)$/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml

# Build Docker image
build:
  stage: build
  image: docker:24
  services:
    - docker:24-dind
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
  script:
    - docker build -t $IMAGE_TAG -t $LATEST_TAG .
    - docker push $IMAGE_TAG
    - docker push $LATEST_TAG
  only:
    - main
    - tags

# Security scan
security_scan:
  stage: build
  image: docker:24
  services:
    - docker:24-dind
  script:
    - docker pull $IMAGE_TAG
    - docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy image --severity HIGH,CRITICAL $IMAGE_TAG
  allow_failure: true
  only:
    - main

# Deploy to Kubernetes
deploy:
  stage: deploy
  image: bitnami/kubectl:latest
  script:
    - kubectl config use-context $KUBE_CONTEXT
    - kubectl set image deployment/app app=$IMAGE_TAG -n production
    - kubectl rollout status deployment/app -n production
  only:
    - main
  when: manual
```

### GitLab CI with Kaniko (No Docker Daemon)

```yaml
# .gitlab-ci.yml using Kaniko

build:
  stage: build
  image:
    name: gcr.io/kaniko-project/executor:debug
    entrypoint: [""]
  script:
    - mkdir -p /kaniko/.docker
    - echo "{\"auths\":{\"$CI_REGISTRY\":{\"auth\":\"$(echo -n $CI_REGISTRY_USER:$CI_REGISTRY_PASSWORD | base64)\"}}}" > /kaniko/.docker/config.json
    - /kaniko/executor
      --context $CI_PROJECT_DIR
      --dockerfile $CI_PROJECT_DIR/Dockerfile
      --destination $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
      --destination $CI_REGISTRY_IMAGE:latest
      --cache=true
  only:
    - main
```

## Jenkins

### Jenkinsfile (Declarative)

```groovy
pipeline {
    agent any

    environment {
        DOCKER_REGISTRY = 'your-registry.com'
        IMAGE_NAME = 'fastapi-app'
        IMAGE_TAG = "${env.BUILD_NUMBER}"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Test') {
            agent {
                docker {
                    image 'python:3.13-slim'
                    args '-v $HOME/.cache/pip:/root/.cache/pip'
                }
            }
            steps {
                sh '''
                    pip install -r requirements.txt
                    pip install -r requirements-dev.txt
                    pytest --cov=. --cov-report=xml
                '''
            }
            post {
                always {
                    junit 'test-results/*.xml'
                    cobertura coberturaReportFile: 'coverage.xml'
                }
            }
        }

        stage('Build') {
            steps {
                script {
                    docker.build("${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}")
                }
            }
        }

        stage('Security Scan') {
            steps {
                sh """
                    docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
                        aquasec/trivy image --severity HIGH,CRITICAL \
                        ${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}
                """
            }
        }

        stage('Push') {
            steps {
                script {
                    docker.withRegistry("https://${DOCKER_REGISTRY}", 'docker-credentials') {
                        docker.image("${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}").push()
                        docker.image("${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}").push('latest')
                    }
                }
            }
        }

        stage('Deploy') {
            when {
                branch 'main'
            }
            steps {
                sh """
                    kubectl set image deployment/app \
                        app=${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} \
                        -n production
                    kubectl rollout status deployment/app -n production
                """
            }
        }
    }

    post {
        always {
            cleanWs()
        }
        success {
            echo 'Pipeline succeeded!'
        }
        failure {
            echo 'Pipeline failed!'
        }
    }
}
```

## CircleCI

```yaml
# .circleci/config.yml

version: 2.1

orbs:
  docker: circleci/docker@2.2.0

jobs:
  test:
    docker:
      - image: cimg/python:3.13
    steps:
      - checkout
      - restore_cache:
          keys:
            - pip-cache-{{ checksum "requirements.txt" }}
      - run:
          name: Install dependencies
          command: |
            pip install -r requirements.txt
            pip install -r requirements-dev.txt
      - save_cache:
          key: pip-cache-{{ checksum "requirements.txt" }}
          paths:
            - ~/.cache/pip
      - run:
          name: Run tests
          command: pytest --cov=. --cov-report=xml
      - store_test_results:
          path: test-results
      - store_artifacts:
          path: coverage.xml

  build-and-push:
    docker:
      - image: cimg/base:stable
    steps:
      - checkout
      - setup_remote_docker:
          docker_layer_caching: true
      - run:
          name: Build Docker image
          command: |
            docker build -t app:${CIRCLE_SHA1} .
      - run:
          name: Test Docker image
          command: |
            docker run -d --name test -p 8000:8000 app:${CIRCLE_SHA1}
            sleep 10
            curl -f http://localhost:8000/health
            docker stop test
      - run:
          name: Push to registry
          command: |
            echo $DOCKER_PASSWORD | docker login -u $DOCKER_USERNAME --password-stdin
            docker tag app:${CIRCLE_SHA1} $DOCKER_USERNAME/app:latest
            docker tag app:${CIRCLE_SHA1} $DOCKER_USERNAME/app:${CIRCLE_SHA1}
            docker push $DOCKER_USERNAME/app:latest
            docker push $DOCKER_USERNAME/app:${CIRCLE_SHA1}

workflows:
  version: 2
  test-build-deploy:
    jobs:
      - test
      - build-and-push:
          requires:
            - test
          filters:
            branches:
              only: main
```

## Best Practices

### 1. Use Build Cache

**GitHub Actions:**
```yaml
- name: Build with cache
  uses: docker/build-push-action@v5
  with:
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

**GitLab CI:**
```yaml
build:
  script:
    - docker build --cache-from $IMAGE_TAG .
```

### 2. Tag Images Properly

```yaml
tags: |
  type=ref,event=branch           # branch name
  type=ref,event=pr               # PR number
  type=semver,pattern={{version}} # v1.0.0
  type=sha,prefix={{branch}}-     # main-abc123
```

### 3. Security Scanning

```yaml
- name: Scan with Trivy
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: app:latest
    severity: 'CRITICAL,HIGH'
    exit-code: '1'  # Fail build on vulnerabilities
```

### 4. Multi-Stage Builds in CI

```dockerfile
# Development stage for testing
FROM python:3.13-slim AS dev
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
RUN pytest

# Production stage
FROM python:3.13-slim AS prod
COPY --from=dev /opt/venv /opt/venv
```

```yaml
# Build dev stage for tests
- docker build --target dev -t app:test .

# Build prod stage for deployment
- docker build --target prod -t app:prod .
```

### 5. Environment-Specific Builds

```yaml
build-dev:
  script:
    - docker build -f Dockerfile.dev -t app:dev .

build-prod:
  script:
    - docker build -f Dockerfile.prod -t app:prod .
  only:
    - main
```

### 6. Secrets Management

**GitHub Actions:**
```yaml
env:
  DB_PASSWORD: ${{ secrets.DB_PASSWORD }}
```

**GitLab CI:**
```yaml
variables:
  DB_PASSWORD: $DB_PASSWORD  # Set in GitLab CI/CD settings
```

**Jenkins:**
```groovy
environment {
    DB_PASSWORD = credentials('db-password')
}
```

### 7. Automated Testing

```yaml
test-image:
  script:
    - docker run -d --name test-app app:latest
    - sleep 10
    - docker exec test-app curl -f http://localhost:8000/health
    - docker logs test-app
    - docker stop test-app
```

## Complete GitHub Actions Example

```yaml
name: Production Docker Pipeline

on:
  push:
    branches: [ main ]
    tags: [ 'v*' ]
  pull_request:
    branches: [ main ]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: '3.13'
    - run: |
        pip install -r requirements.txt -r requirements-dev.txt
        pytest --cov=. --cov-report=xml
    - uses: codecov/codecov-action@v3

  build:
    needs: test
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
      security-events: write
    steps:
    - uses: actions/checkout@v4

    - uses: docker/setup-buildx-action@v3

    - uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    - id: meta
      uses: docker/metadata-action@v5
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
        tags: |
          type=ref,event=branch
          type=semver,pattern={{version}}
          type=sha

    - uses: docker/build-push-action@v5
      with:
        context: .
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

    - uses: aquasecurity/trivy-action@master
      with:
        image-ref: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
        format: 'sarif'
        output: 'trivy-results.sarif'

    - uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: 'trivy-results.sarif'

  deploy:
    needs: build
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
    - uses: azure/k8s-set-context@v3
      with:
        kubeconfig: ${{ secrets.KUBE_CONFIG }}
    - run: |
        kubectl set image deployment/app app=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }} -n production
        kubectl rollout status deployment/app -n production
```

## References

- [GitHub Actions Docker Guide](https://docs.github.com/en/actions/publishing-packages/publishing-docker-images)
- [GitLab CI Docker Integration](https://docs.gitlab.com/ee/ci/docker/)
- [Jenkins Docker Pipeline](https://www.jenkins.io/doc/book/pipeline/docker/)
- [CircleCI Docker](https://circleci.com/docs/docker/)
