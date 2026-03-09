# Kubernetes API Interaction with Python

## Project Overview
**Difficulty:** Intermediate  
**Estimated Time:** 4 hours  
**Skills Practiced:** Python, Kubernetes API, kubectl, Container Orchestration

### What You'll Build
A Python tool that interacts with Kubernetes clusters to:
- Authenticate using tokens or kubeconfig
- List pods, deployments, services across namespaces
- Scale deployments up/down programmatically
- Retrieve pod logs for debugging
- Monitor cluster resource usage
- Execute commands inside pods

### Why This Matters
Modern applications run on Kubernetes. This project teaches you to programmatically manage K8s resources—essential for automation, monitoring, and building custom operational tools.

### Prerequisites
- Python 3.8+ installed
- Kubernetes cluster access (minikube, kind, or cloud K8s)
- kubectl installed and configured
- Basic Kubernetes concepts (pods, deployments, services)

---

## Step-by-Step Implementation

### Step 1: Set Up Kubernetes Cluster

**Using minikube (local testing):**
```bash
# Install minikube
brew install minikube  # macOS
# or: choco install minikube  # Windows

# Start cluster
minikube start --driver=docker

# Verify
kubectl cluster-info
kubectl get nodes
```

**Using kind (Kubernetes in Docker):**
```bash
# Install kind
brew install kind

# Create cluster
kind create cluster --name devops-practice

# Verify
kubectl cluster-info --context kind-devops-practice
```

### Step 2: Project Setup
```bash
mkdir k8s-python-manager
cd k8s-python-manager
python3 -m venv venv
source venv/bin/activate
pip install kubernetes pyyaml tabulate
```

### Step 3: Configure Kubernetes Client

Create `k8s_manager.py`:
```python
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import os

class K8sManager:
    def __init__(self, kubeconfig_path=None):
        """Initialize Kubernetes client"""
        try:
            # Try in-cluster config first (when running inside K8s)
            config.load_incluster_config()
            print("✓ Using in-cluster configuration")
        except:
            # Fall back to kubeconfig file
            if kubeconfig_path:
                config.load_kube_config(config_file=kubeconfig_path)
            else:
                config.load_kube_config()
            print("✓ Using kubeconfig file")

        self.v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()

    def get_namespaces(self):
        """List all namespaces"""
        try:
            namespaces = self.v1.list_namespace()
            return [ns.metadata.name for ns in namespaces.items]
        except ApiException as e:
            print(f"Error listing namespaces: {e}")
            return []
```

### Step 4: Implement Pod Management

```python
def list_pods(self, namespace='default', label_selector=None):
    """List pods in namespace with optional label filter"""
    try:
        if label_selector:
            pods = self.v1.list_namespaced_pod(
                namespace=namespace,
                label_selector=label_selector
            )
        else:
            pods = self.v1.list_namespaced_pod(namespace=namespace)

        pod_list = []
        for pod in pods.items:
            pod_info = {
                'name': pod.metadata.name,
                'namespace': pod.metadata.namespace,
                'status': pod.status.phase,
                'ip': pod.status.pod_ip,
                'node': pod.spec.node_name,
                'restarts': sum(cs.restart_count for cs in pod.status.container_statuses or [])
            }
            pod_list.append(pod_info)

        return pod_list
    except ApiException as e:
        print(f"Error listing pods: {e}")
        return []

def get_pod_logs(self, pod_name, namespace='default', container=None, tail_lines=100):
    """Fetch logs from a pod"""
    try:
        if container:
            logs = self.v1.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                container=container,
                tail_lines=tail_lines
            )
        else:
            logs = self.v1.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                tail_lines=tail_lines
            )
        return logs
    except ApiException as e:
        print(f"Error fetching logs: {e}")
        return None

def delete_pod(self, pod_name, namespace='default'):
    """Delete a pod"""
    try:
        self.v1.delete_namespaced_pod(
            name=pod_name,
            namespace=namespace
        )
        print(f"✓ Deleted pod: {pod_name}")
        return True
    except ApiException as e:
        print(f"✗ Error deleting pod: {e}")
        return False
```

### Step 5: Implement Deployment Management

```python
def list_deployments(self, namespace='default'):
    """List deployments in namespace"""
    try:
        deployments = self.apps_v1.list_namespaced_deployment(namespace=namespace)

        deploy_list = []
        for deploy in deployments.items:
            deploy_info = {
                'name': deploy.metadata.name,
                'namespace': deploy.metadata.namespace,
                'replicas': deploy.spec.replicas,
                'ready': deploy.status.ready_replicas or 0,
                'available': deploy.status.available_replicas or 0,
                'image': deploy.spec.template.spec.containers[0].image
            }
            deploy_list.append(deploy_info)

        return deploy_list
    except ApiException as e:
        print(f"Error listing deployments: {e}")
        return []

def scale_deployment(self, deployment_name, replicas, namespace='default'):
    """Scale deployment to specified replica count"""
    try:
        # Patch the deployment
        body = {'spec': {'replicas': replicas}}
        self.apps_v1.patch_namespaced_deployment_scale(
            name=deployment_name,
            namespace=namespace,
            body=body
        )
        print(f"✓ Scaled {deployment_name} to {replicas} replicas")
        return True
    except ApiException as e:
        print(f"✗ Error scaling deployment: {e}")
        return False

def restart_deployment(self, deployment_name, namespace='default'):
    """Restart deployment by updating annotation"""
    try:
        from datetime import datetime

        # Get current deployment
        deployment = self.apps_v1.read_namespaced_deployment(
            name=deployment_name,
            namespace=namespace
        )

        # Add/update restart annotation
        if deployment.spec.template.metadata.annotations is None:
            deployment.spec.template.metadata.annotations = {}

        deployment.spec.template.metadata.annotations['kubectl.kubernetes.io/restartedAt'] =             datetime.now().isoformat()

        # Patch deployment
        self.apps_v1.patch_namespaced_deployment(
            name=deployment_name,
            namespace=namespace,
            body=deployment
        )
        print(f"✓ Restarted deployment: {deployment_name}")
        return True
    except ApiException as e:
        print(f"✗ Error restarting deployment: {e}")
        return False
```

### Step 6: Implement Service Management

```python
def list_services(self, namespace='default'):
    """List services in namespace"""
    try:
        services = self.v1.list_namespaced_service(namespace=namespace)

        svc_list = []
        for svc in services.items:
            svc_info = {
                'name': svc.metadata.name,
                'namespace': svc.metadata.namespace,
                'type': svc.spec.type,
                'cluster_ip': svc.spec.cluster_ip,
                'ports': [f"{p.port}/{p.protocol}" for p in svc.spec.ports]
            }
            svc_list.append(svc_info)

        return svc_list
    except ApiException as e:
        print(f"Error listing services: {e}")
        return []
```

### Step 7: Add Cluster Resource Monitoring

```python
def get_cluster_resources(self):
    """Get cluster-wide resource usage"""
    try:
        nodes = self.v1.list_node()

        node_info = []
        for node in nodes.items:
            allocatable = node.status.allocatable
            capacity = node.status.capacity

            info = {
                'name': node.metadata.name,
                'status': 'Ready' if any(c.type == 'Ready' and c.status == 'True' 
                                        for c in node.status.conditions) else 'NotReady',
                'cpu_allocatable': allocatable.get('cpu', 'N/A'),
                'memory_allocatable': allocatable.get('memory', 'N/A'),
                'pods_allocatable': allocatable.get('pods', 'N/A')
            }
            node_info.append(info)

        return node_info
    except ApiException as e:
        print(f"Error getting cluster resources: {e}")
        return []
```

### Step 8: Create CLI Interface

```python
import argparse
from tabulate import tabulate

def main():
    parser = argparse.ArgumentParser(description='Kubernetes Cluster Manager')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Pod commands
    pod_parser = subparsers.add_parser('pods', help='Manage pods')
    pod_parser.add_argument('--namespace', '-n', default='default')
    pod_parser.add_argument('--labels', '-l', help='Label selector')

    # Deployment commands
    deploy_parser = subparsers.add_parser('deployments', help='Manage deployments')
    deploy_parser.add_argument('--namespace', '-n', default='default')

    # Scale command
    scale_parser = subparsers.add_parser('scale', help='Scale deployment')
    scale_parser.add_argument('deployment', help='Deployment name')
    scale_parser.add_argument('replicas', type=int, help='Number of replicas')
    scale_parser.add_argument('--namespace', '-n', default='default')

    # Logs command
    logs_parser = subparsers.add_parser('logs', help='Get pod logs')
    logs_parser.add_argument('pod', help='Pod name')
    logs_parser.add_argument('--namespace', '-n', default='default')
    logs_parser.add_argument('--tail', type=int, default=100)

    # Cluster command
    subparsers.add_parser('cluster', help='Show cluster info')

    args = parser.parse_args()

    # Initialize manager
    manager = K8sManager()

    # Execute commands
    if args.command == 'pods':
        pods = manager.list_pods(args.namespace, args.labels)
        print(f"\nPods in namespace '{args.namespace}':")
        print(tabulate(pods, headers='keys', tablefmt='grid'))

    elif args.command == 'deployments':
        deployments = manager.list_deployments(args.namespace)
        print(f"\nDeployments in namespace '{args.namespace}':")
        print(tabulate(deployments, headers='keys', tablefmt='grid'))

    elif args.command == 'scale':
        manager.scale_deployment(args.deployment, args.replicas, args.namespace)

    elif args.command == 'logs':
        logs = manager.get_pod_logs(args.pod, args.namespace, tail_lines=args.tail)
        print(f"\nLogs for pod '{args.pod}':")
        print(logs)

    elif args.command == 'cluster':
        nodes = manager.get_cluster_resources()
        print("\nCluster Nodes:")
        print(tabulate(nodes, headers='keys', tablefmt='grid'))

if __name__ == "__main__":
    main()
```

### Step 9: Create Test Deployment

Create `test-deployment.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-test
  labels:
    app: nginx
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:latest
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: nginx-service
spec:
  selector:
    app: nginx
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP
```

Deploy test resources:
```bash
kubectl apply -f test-deployment.yaml
```

### Step 10: Test Your Implementation

```bash
# List all pods
python k8s_manager.py pods

# List pods in specific namespace
python k8s_manager.py pods -n kube-system

# List deployments
python k8s_manager.py deployments

# Scale deployment
python k8s_manager.py scale nginx-test 5

# Get pod logs
python k8s_manager.py logs nginx-test-<pod-id>

# Show cluster info
python k8s_manager.py cluster
```

---

## Success Criteria
- [ ] Successfully connects to Kubernetes cluster
- [ ] Lists pods, deployments, and services
- [ ] Scales deployments up and down
- [ ] Retrieves pod logs
- [ ] Monitors cluster resource usage
- [ ] Handles API errors gracefully

## Extension Ideas
1. **Resource Creation:** Create pods/deployments via Python
2. **Health Monitoring:** Automated health checks and alerts
3. **Auto-Scaling:** Implement custom HPA logic
4. **Multi-Cluster:** Manage multiple K8s clusters
5. **Resource Cleanup:** Auto-delete old/unused resources
6. **Metrics Collection:** Integrate with Prometheus metrics
7. **GitOps Integration:** Deploy from Git repositories

## Common Issues

**Issue:** Unable to connect to cluster  
**Solution:** Verify kubectl works: `kubectl get nodes`

**Issue:** Permission denied errors  
**Solution:** Check RBAC permissions and service account

**Issue:** Module 'kubernetes' not found  
**Solution:** Ensure correct venv activation and package install

---

**Completion Time:** 4 hours  
**Difficulty:** Intermediate  
**Next Project:** Custom CLI Tool
