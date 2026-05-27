# Bookinfo 微服务智能监控问答助手演示文档

这是一份“从零启动到完成演示”的完整文档。

如果你执行：

```powershell
kubectl get pods -n bookinfo
```

看到：

```text
No resources found in bookinfo namespace.
```

说明 `Bookinfo` 还没有部署，或者之前的环境已经被清掉了。  
这种情况下，不要直接开始演示，要先按下面步骤把环境重新拉起来。

---

## 1. 演示目标

这次演示要证明 4 件事：

1. 我们的系统接的是 **真实 Bookinfo + 真实 Prometheus**
2. 用户可以直接用自然语言提问
3. 系统会自动选择工具、自动生成 `PromQL`
4. 当我们人为改变微服务状态后，系统确实能检测出变化

---

## 2. 你需要的目录

### 项目目录

```text
<PROJECT_DIR>
```

### Istio 目录

```text
<ISTIO_DIR>
```

下面文档里的命令都用占位符表示，你在自己电脑上只需要替换：

- `<PROJECT_DIR>`：你的项目目录
- `<ISTIO_DIR>`：你的 Istio 根目录

---

## 3. 第 0 步：打开 4 个终端

建议你提前开好 4 个 PowerShell 窗口，分别用来做：

1. 启动/检查 Kubernetes 与 Istio
2. `productpage` 端口转发
3. `Prometheus` 端口转发
4. 启动本项目和做流量/故障操作

---

## 4. 第 1 步：确认基础环境

在任意终端执行：

```powershell
python --version
python -m streamlit --version
kubectl cluster-info
```

### 你要讲的内容

“这里先确认 Python、Streamlit 和 Kubernetes 集群本身可用。我们的系统前端是 Streamlit，真实数据来自 Kubernetes 上运行的 Bookinfo 和 Istio Prometheus。”

---

## 5. 第 2 步：先判断环境是不是空的

执行：

```powershell
kubectl get ns
kubectl get pods -n istio-system
kubectl get pods -n bookinfo
```

### 两种情况

#### 情况 A：已经有资源

如果你看到：

- `istio-system` 里有 `istiod`、`istio-ingressgateway`、`prometheus`
- `bookinfo` 里有 `productpage`、`details`、`ratings`、`reviews`

那就说明环境已经起来了，可以直接跳到第 9 步。

#### 情况 B：没有资源

如果你看到：

```text
No resources found in bookinfo namespace.
```

或者 `istio-system` 里也没有东西，那就按第 6 到第 8 步，从零启动。

---

## 6. 第 3 步：从零安装 Istio

### 6.1 先确认 `istioctl` 存在

执行：

```powershell
& "<ISTIO_DIR>\bin\istioctl.exe" version
```

### 6.2 安装 Istio demo profile

执行：

```powershell
& "<ISTIO_DIR>\bin\istioctl.exe" install --set profile=demo -y
```

### 6.3 验证 Istio

执行：

```powershell
kubectl get pods -n istio-system
```

### 预期结果

至少能看到这些 Pod 为 `Running`：

- `istiod`
- `istio-ingressgateway`
- `istio-egressgateway`

### 讲解词

“如果环境是空的，我会先安装 Istio，因为 Bookinfo 的服务治理和监控依赖 Istio 控制面以及它提供的可观测能力。”

---

## 7. 第 4 步：部署 Bookinfo

### 7.1 创建命名空间

执行：

```powershell
kubectl create namespace bookinfo
```

如果提示已存在也没关系。

### 7.2 开启 sidecar 注入

执行：

```powershell
kubectl label namespace bookinfo istio-injection=enabled --overwrite
```

### 7.3 部署 Bookinfo 应用

执行：

```powershell
kubectl apply -n bookinfo -f "<ISTIO_DIR>\samples\bookinfo\platform\kube\bookinfo.yaml"
```

### 7.4 部署网关规则

执行：

```powershell
kubectl apply -n bookinfo -f "<ISTIO_DIR>\samples\bookinfo\networking\bookinfo-gateway.yaml"
```

### 7.5 验证 Bookinfo

执行：

```powershell
kubectl get pods -n bookinfo
kubectl get svc -n bookinfo
```

### 预期结果

Pod 中应出现并运行：

- `details-v1`
- `ratings-v1`
- `reviews-v1`
- `reviews-v2`
- `reviews-v3`
- `productpage-v1`

### 讲解词

“这里把 Bookinfo 真正部署到 Kubernetes 中，并开启 Istio sidecar 注入，保证后面 Prometheus 可以采集到 Istio 相关的真实流量指标。”

---

## 8. 第 5 步：部署 Prometheus

### 操作

执行：

```powershell
kubectl apply -f "<ISTIO_DIR>\samples\addons\prometheus.yaml"
```

然后执行：

```powershell
kubectl get pods -n istio-system
```

### 预期结果

你应该能看到：

- `prometheus`

并且状态是 `Running`

### 讲解词

“这里部署的是 Istio 自带的 Prometheus，用来作为我们的真实监控数据源。”

---

## 9. 第 6 步：打开真实环境访问通道

### 终端 A：转发 productpage

```powershell
kubectl -n bookinfo port-forward svc/productpage 9080:9080
```

### 终端 B：转发 Prometheus

```powershell
kubectl -n istio-system port-forward svc/prometheus 9090:9090
```

### 终端 C：启动项目

```powershell
cd <PROJECT_DIR>
python -m streamlit run app.py
```

### 浏览器地址

```text
http://localhost:8501
http://127.0.0.1:9080/productpage
http://127.0.0.1:9090
```

### 讲解词

“这里分别打通业务入口、Prometheus 数据源和我们自己的问答页面，这样后面整条监控链路都可以现场展示。”

---

## 10. 第 7 步：验证真实环境可用

### 验证 productpage

浏览器打开：

```text
http://127.0.0.1:9080/productpage
```

### 验证 Prometheus

浏览器打开：

```text
http://127.0.0.1:9090
```

### 讲解词

“这一步确认真实业务和真实监控系统都可达，所以后面所有查询都不是模拟数据。”

---

## 11. 第 8 步：进入页面并切换到真实环境

浏览器打开：

```text
http://localhost:8501
```

左侧边栏选择：

- `Data Mode` -> `Real Environment`

### 讲解词

“现在切到真实环境模式，后续所有回答都来自真实 Prometheus 指标。”

---

## 12. 第 9 步：先做一份基线快照

### 操作

点击左侧按钮：

```text
Capture Baseline Snapshot
```

### 讲解词

“我先抓取一份当前集群的基线快照，后面做流量变化和延迟注入后，就可以做前后对比，而不是只看单次结果。”

---

## 13. 第 10 步：展示工具注册表

点击：

```text
Tool Registry
```

### 讲解词

“这里展示的是工具注册表。我们不是直接硬编码问答，而是先把 Prometheus 查询能力封装成语义明确的工具，再由系统自动选择。”

---

## 14. 第 11 步：先做基线查询

回到 `QA` 页面，先问两个问题。

### 问题 1

```text
details 最近 5 分钟请求量怎么样？
```

### 问题 2

```text
reviews 的延迟高不高？
```

### 页面上要讲的点

按顺序展示：

1. `Parsed Result`
2. `Selected Tools`
3. `Generated PromQL`
4. `Answer`

### 讲解词

“这一步先查看真实环境的当前基线状态。这里我优先选择 details 的请求量，因为这条指标在 Istio 服务间调用里通常更稳定，更适合课堂演示。系统会自动识别问题类型，选择工具，生成 PromQL，并返回真实监控结果。”

---

## 15. 第 12 步：人为制造流量变化

### 方案一：用页面按钮

直接点击左侧：

```text
Warm Traffic
```

### 方案二：手动命令

在终端执行：

```powershell
for ($i=0; $i -lt 80; $i++) { Invoke-WebRequest -UseBasicParsing http://127.0.0.1:9080/productpage | Out-Null }
```

### 讲解词

“这里我主动向 productpage 打一批真实请求，让请求速率发生变化。后面再次提问时，系统应该能检测到这个变化。”

---

## 16. 第 13 步：再次提问，验证请求量变化

再次输入：

```text
details 最近 5 分钟请求量怎么样？
```

### 要重点展示

- 新的回答结果
- `Before/After Snapshot`
- `Observed changes`

### 讲解词

“现在再次查询同一个问题。因为刚才真实发起了一批请求，所以系统检测到的请求量会比基线更高，而且下方会显示前后快照对比。”

---

## 17. 第 14 步：人为制造延迟变化

### 方案一：用页面按钮

点击：

```text
Inject Delay Fault
```

### 方案二：手动命令

执行：

```powershell
kubectl apply -n bookinfo -f "<ISTIO_DIR>\samples\bookinfo\networking\virtual-service-ratings-test-delay.yaml"
```

然后再打一轮流量：

```powershell
for ($i=0; $i -lt 40; $i++) { Invoke-WebRequest -UseBasicParsing http://127.0.0.1:9080/productpage | Out-Null }
```

### 讲解词

“这里我通过 Istio 的流量治理能力，向真实业务链路注入延迟，再打一轮流量，让 Prometheus 采集到变化后的延迟指标。”

---

## 18. 第 15 步：再次提问，验证延迟变化

输入：

```text
reviews 的延迟高不高？
```

或者：

```text
reviews 最近 5 分钟延迟趋势如何？
```

### 要重点展示

- 回答中的延迟结论
- `Service Assessment`
- `Before/After Snapshot`

### 讲解词

“现在系统能检测到服务延迟已经发生变化，而且不仅返回数值，还会给出服务级判断和建议。”

---

## 19. 第 16 步：生成健康报告

点击：

```text
Health Report
```

再点击：

```text
Generate Health Report
```

### 要重点展示

- `Overall Status`
- `Highest-risk service`
- `Risk Notes`
- `Suggestions`

### 讲解词

“健康报告会把多个真实指标汇总分析，不只是回答一个点问题，而是给出整个 Bookinfo 的状态判断，指出风险最高的服务和对应建议。”

---

## 20. 第 17 步：恢复环境

### 方案一：用页面按钮

点击：

```text
Reset Traffic Rules
```

### 方案二：手动命令

执行：

```powershell
kubectl apply -n bookinfo -f "<ISTIO_DIR>\samples\bookinfo\networking\virtual-service-all.yaml"
```

### 讲解词

“演示结束后把流量规则恢复，保证环境回到正常状态。”

---

## 21. 最短可执行流程

如果你时间很紧，可以只按这套最短流程走：

### 21.1 如果环境没起

```powershell
& "<ISTIO_DIR>\bin\istioctl.exe" install --set profile=demo -y
kubectl create namespace bookinfo
kubectl label namespace bookinfo istio-injection=enabled --overwrite
kubectl apply -n bookinfo -f "<ISTIO_DIR>\samples\bookinfo\platform\kube\bookinfo.yaml"
kubectl apply -n bookinfo -f "<ISTIO_DIR>\samples\bookinfo\networking\bookinfo-gateway.yaml"
kubectl apply -f "<ISTIO_DIR>\samples\addons\prometheus.yaml"
```

### 21.2 打开转发

```powershell
kubectl -n bookinfo port-forward svc/productpage 9080:9080
kubectl -n istio-system port-forward svc/prometheus 9090:9090
```

### 21.3 启动项目

```powershell
cd <PROJECT_DIR>
python -m streamlit run app.py
```

### 21.4 开始演示

1. `Capture Baseline Snapshot`
2. 问 `details 最近 5 分钟请求量怎么样？`
3. `Warm Traffic`
4. 再问同一个问题
5. `Inject Delay Fault`
6. 问 `reviews 的延迟高不高？`
7. `Generate Health Report`

---

## 22. 上台可以直接说的话

“老师好，我演示的项目是 Bookinfo 微服务智能监控问答助手。这个系统接的是 Kubernetes 中真实运行的 Bookinfo 服务和真实 Prometheus 指标。系统先把 Prometheus 查询能力封装成多个语义化工具，再通过自然语言完成问题解析、工具选择、PromQL 生成和结果分析。”

“为了证明它不是静态展示，我会先抓取一份基线快照，然后主动制造请求流量和链路延迟，再重新提问。大家可以看到系统返回的结果会跟着真实微服务状态变化，这说明它确实具有实际监控分析能力。”  
