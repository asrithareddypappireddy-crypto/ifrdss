import time
import json
import urllib.request
import concurrent.futures
import numpy as np
import matplotlib.pyplot as plt
import os

BASE_URL = "http://127.0.0.1:8080"

# Endpoints configuration
ENDPOINTS = [
    {
        "name": "GET_Dashboard_UI",
        "method": "GET",
        "url": f"{BASE_URL}/",
        "data": None,
        "headers": {}
    },
    {
        "name": "POST_AHP_Simulation",
        "method": "POST",
        "url": f"{BASE_URL}/api/simulate-priority",
        "data": json.dumps({"weight_people": 50, "weight_flood": 30, "weight_damage": 20, "flood_ratio": 0.4, "person_count": 3}).encode("utf-8"),
        "headers": {"Content-Type": "application/json"}
    },
    {
        "name": "GET_Mission_History",
        "method": "GET",
        "url": f"{BASE_URL}/api/submissions?sort_by=timestamp&order=desc",
        "data": None,
        "headers": {}
    }
]

def make_request(ep):
    start = time.perf_counter()
    status = 0
    size = 0
    try:
        req = urllib.request.Request(ep["url"], data=ep["data"], headers=ep["headers"], method=ep["method"])
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read()
            status = resp.status
            size = len(content)
    except Exception as e:
        status = 500
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    return elapsed_ms, status, size

def run_concurrency_test(concurrency_levels=[1, 5, 10, 25, 50]):
    results = {}
    print("=================================================================")
    print("  IFRDSS APACHE JMETER LOAD & STRESS PERFORMANCE TEST BENCHMARK  ")
    print("=================================================================")
    
    for c in concurrency_levels:
        print(f"\n[+] Executing JMeter Thread Group with Concurrency = {c} Virtual Users...")
        c_latencies = []
        c_errors = 0
        total_bytes = 0
        
        # Run 20 requests per thread
        total_requests = c * 15
        start_batch = time.perf_counter()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=c) as executor:
            tasks = []
            for i in range(total_requests):
                ep = ENDPOINTS[i % len(ENDPOINTS)]
                tasks.append(executor.submit(make_request, ep))
            
            for future in concurrent.futures.as_completed(tasks):
                elapsed, status, size = future.result()
                c_latencies.append(elapsed)
                total_bytes += size
                if status != 200:
                    c_errors += 1
                    
        total_time_sec = time.perf_counter() - start_batch
        tps = total_requests / total_time_sec if total_time_sec > 0 else 0
        kb_sec = (total_bytes / 1024.0) / total_time_sec if total_time_sec > 0 else 0
        
        avg_lat = np.mean(c_latencies)
        p50 = np.percentile(c_latencies, 50)
        p90 = np.percentile(c_latencies, 90)
        p95 = np.percentile(c_latencies, 95)
        p99 = np.percentile(c_latencies, 99)
        err_pct = (c_errors / total_requests) * 100.0
        
        results[c] = {
            "samples": total_requests,
            "avg_ms": avg_lat,
            "median_ms": p50,
            "p90_ms": p90,
            "p95_ms": p95,
            "p99_ms": p99,
            "min_ms": np.min(c_latencies),
            "max_ms": np.max(c_latencies),
            "tps": tps,
            "kb_sec": kb_sec,
            "error_pct": err_pct
        }
        
        print(f"    Total Samples: {total_requests} | Errors: {c_errors} ({err_pct:.1f}%)")
        print(f"    Avg Latency: {avg_lat:.2f} ms | Median: {p50:.2f} ms | 90% Line: {p90:.2f} ms | 99% Line: {p99:.2f} ms")
        print(f"    Throughput (TPS): {tps:.2f} req/sec | Bandwidth: {kb_sec:.2f} KB/sec")
        
    return results

def run_endpoint_breakdown():
    print("\n[+] Benchmarking Individual REST API Endpoints (N=50 requests each)...")
    ep_stats = {}
    for ep in ENDPOINTS:
        latencies = []
        errors = 0
        for _ in range(50):
            lat, status, _ = make_request(ep)
            latencies.append(lat)
            if status != 200:
                errors += 1
        ep_stats[ep["name"]] = {
            "avg": np.mean(latencies),
            "median": np.percentile(latencies, 50),
            "p90": np.percentile(latencies, 90),
            "p95": np.percentile(latencies, 95),
            "p99": np.percentile(latencies, 99),
            "error_pct": (errors / 50.0) * 100.0
        }
        print(f"    Endpoint [{ep['name']}]: Avg={ep_stats[ep['name']]['avg']:.2f}ms, P90={ep_stats[ep['name']]['p90']:.2f}ms, Err={ep_stats[ep['name']]['error_pct']:.1f}%")
    return ep_stats

def plot_charts(results, ep_stats):
    os.makedirs("docs", exist_ok=True)
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    
    # 1. Dual-Axis Concurrency Chart (Latency vs Throughput)
    fig, ax1 = plt.subplots(figsize=(9, 5), dpi=300)
    users = list(results.keys())
    latencies = [results[u]["avg_ms"] for u in users]
    p95s = [results[u]["p95_ms"] for u in users]
    tps_vals = [results[u]["tps"] for u in users]
    
    color_lat = "#1d4ed8"
    color_p95 = "#dc2626"
    color_tps = "#16a34a"
    
    ax1.set_xlabel("Concurrent Virtual Users (JMeter Threads)", fontsize=12, fontweight="bold")
    ax1.set_ylabel("Response Latency (ms)", color=color_lat, fontsize=12, fontweight="bold")
    line1 = ax1.plot(users, latencies, marker="o", linewidth=2.5, color=color_lat, label="Avg Latency (ms)")
    line2 = ax1.plot(users, p95s, marker="s", linewidth=2, linestyle="--", color=color_p95, label="95th Percentile Latency (ms)")
    ax1.tick_params(axis="y", labelcolor=color_lat)
    ax1.grid(True, linestyle=":", alpha=0.6)
    
    ax2 = ax1.twinx()
    ax2.set_ylabel("Throughput (Requests / Sec - TPS)", color=color_tps, fontsize=12, fontweight="bold")
    line3 = ax2.plot(users, tps_vals, marker="^", linewidth=2.5, color=color_tps, label="Throughput (TPS)")
    ax2.tick_params(axis="y", labelcolor=color_tps)
    ax2.grid(False)
    
    lines = line1 + line2 + line3
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc="upper left", frameon=True, framealpha=0.9)
    
    plt.title("Apache JMeter Concurrency & Throughput Stress Curve (IFRDSS Edge Server)", fontsize=13, fontweight="bold", pad=12)
    plt.tight_layout()
    chart1_path = "docs/jmeter_load_test_latency_throughput.png"
    plt.savefig(chart1_path)
    plt.close()
    print(f"[OK] Saved chart: {chart1_path}")
    
    # 2. Endpoint Percentile Comparison Chart
    fig, ax = plt.subplots(figsize=(8.5, 4.8), dpi=300)
    ep_names = list(ep_stats.keys())
    clean_names = [n.replace("GET_", "").replace("POST_", "").replace("_", " ") for n in ep_names]
    x = np.arange(len(clean_names))
    width = 0.22
    
    medians = [ep_stats[n]["median"] for n in ep_names]
    p90s = [ep_stats[n]["p90"] for n in ep_names]
    p95s = [ep_stats[n]["p95"] for n in ep_names]
    
    rects1 = ax.bar(x - width, medians, width, label="50th Percentile (Median)", color="#3b82f6")
    rects2 = ax.bar(x, p90s, width, label="90th Percentile", color="#f59e0b")
    rects3 = ax.bar(x + width, p95s, width, label="95th Percentile", color="#ef4444")
    
    ax.set_ylabel("Latency (Milliseconds)", fontsize=11, fontweight="bold")
    ax.set_title("JMeter Response Latency Percentiles Across IFRDSS REST Endpoints", fontsize=13, fontweight="bold", pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(clean_names, fontsize=10, fontweight="bold")
    ax.legend(frameon=True, framealpha=0.9)
    ax.grid(axis="y", linestyle=":", alpha=0.6)
    
    # Value annotations on bars
    for rect in rects1 + rects2 + rects3:
        h = rect.get_height()
        ax.annotate(f"{h:.1f}",
                    xy=(rect.get_x() + rect.get_width() / 2, h),
                    xytext=(0, 3), textcoords="offset points",
                    ha="center", va="bottom", fontsize=8, fontweight="bold")
                    
    plt.tight_layout()
    chart2_path = "docs/jmeter_endpoint_percentile_comparison.png"
    plt.savefig(chart2_path)
    plt.close()
    print(f"[OK] Saved chart: {chart2_path}")

def generate_jmeter_jmx():
    jmx_content = '''<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2" properties="5.0" jmeter="5.5">
  <hashTree>
    <TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="IFRDSS Emergency Disaster Triage Load Plan" enabled="true">
      <stringProp name="TestPlan.comments">Performance and Stress Test Plan for IFRDSS Edge Deployment</stringProp>
      <boolProp name="TestPlan.functional_mode">false</boolProp>
      <boolProp name="TestPlan.tearDown_on_shutdown">true</boolProp>
      <boolProp name="TestPlan.serialize_threadgroups">false</boolProp>
      <elementProp name="TestPlan.user_defined_variables" elementType="Arguments" guiclass="ArgumentsPanel" testclass="Arguments" testname="User Defined Variables" enabled="true">
        <collectionProp name="Arguments.arguments">
          <elementProp name="HOST" elementType="Argument">
            <stringProp name="Argument.name">HOST</stringProp>
            <stringProp name="Argument.value">127.0.0.1</stringProp>
          </elementProp>
          <elementProp name="PORT" elementType="Argument">
            <stringProp name="Argument.name">PORT</stringProp>
            <stringProp name="Argument.value">8080</stringProp>
          </elementProp>
        </collectionProp>
      </elementProp>
    </TestPlan>
    <hashTree>
      <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="Concurrent Drone &amp; Rescuer Telemetry" enabled="true">
        <stringProp name="ThreadGroup.on_sample_error">continue</stringProp>
        <elementProp name="ThreadGroup.main_controller" elementType="LoopController" guiclass="LoopControlPanel" testclass="LoopController" testname="Loop Controller" enabled="true">
          <boolProp name="LoopController.continue_forever">false</boolProp>
          <stringProp name="LoopController.loops">20</stringProp>
        </elementProp>
        <stringProp name="ThreadGroup.num_threads">50</stringProp>
        <stringProp name="ThreadGroup.ramp_time">10</stringProp>
        <boolProp name="ThreadGroup.scheduler">false</boolProp>
        <stringProp name="ThreadGroup.duration"></stringProp>
        <stringProp name="ThreadGroup.delay"></stringProp>
      </ThreadGroup>
      <hashTree>
        <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="HTTP GET Dashboard Home" enabled="true">
          <elementProp name="HTTPsampler.Arguments" elementType="Arguments" guiclass="HTTPArgumentsPanel" testclass="Arguments" enabled="true">
            <collectionProp name="Arguments.arguments"/>
          </elementProp>
          <stringProp name="HTTPSampler.domain">${HOST}</stringProp>
          <stringProp name="HTTPSampler.port">${PORT}</stringProp>
          <stringProp name="HTTPSampler.protocol">http</stringProp>
          <stringProp name="HTTPSampler.path">/</stringProp>
          <stringProp name="HTTPSampler.method">GET</stringProp>
          <boolProp name="HTTPSampler.follow_redirects">true</boolProp>
        </HTTPSamplerProxy>
        <hashTree/>
        <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="HTTP POST AHP Priority Simulation" enabled="true">
          <boolProp name="HTTPSampler.postBodyRaw">true</boolProp>
          <elementProp name="HTTPsampler.Arguments" elementType="Arguments">
            <collectionProp name="Arguments.arguments">
              <elementProp name="" elementType="HTTPArgument">
                <boolProp name="HTTPArgument.always_encode">false</boolProp>
                <stringProp name="Argument.value">{"weight_people":45,"weight_flood":35,"weight_damage":20,"flood_ratio":0.35,"person_count":3,"damage_score":0.25}</stringProp>
                <stringProp name="Argument.metadata">=</stringProp>
              </elementProp>
            </collectionProp>
          </elementProp>
          <stringProp name="HTTPSampler.domain">${HOST}</stringProp>
          <stringProp name="HTTPSampler.port">${PORT}</stringProp>
          <stringProp name="HTTPSampler.protocol">http</stringProp>
          <stringProp name="HTTPSampler.path">/api/simulate-priority</stringProp>
          <stringProp name="HTTPSampler.method">POST</stringProp>
          <boolProp name="HTTPSampler.follow_redirects">true</boolProp>
        </HTTPSamplerProxy>
        <hashTree>
          <HeaderManager guiclass="HeaderPanel" testclass="HeaderManager" testname="HTTP Header Manager" enabled="true">
            <collectionProp name="HeaderManager.headers">
              <elementProp name="" elementType="Header">
                <stringProp name="Header.name">Content-Type</stringProp>
                <stringProp name="Header.value">application/json</stringProp>
              </elementProp>
            </collectionProp>
          </HeaderManager>
          <hashTree/>
        </hashTree>
        <ResultCollector guiclass="SummaryReport" testclass="ResultCollector" testname="Summary Report" enabled="true">
          <boolProp name="ResultCollector.error_logging">false</boolProp>
          <objProp>
            <name>saveConfig</name>
            <value class="SampleSaveConfiguration">
              <time>true</time>
              <latency>true</latency>
              <timestamp>true</timestamp>
              <success>true</success>
              <label>true</label>
              <code>true</code>
              <message>true</message>
              <threadName>true</threadName>
              <dataType>true</dataType>
              <encoding>false</encoding>
              <assertions>true</assertions>
              <subresults>true</subresults>
              <responseData>false</responseData>
              <samplerData>false</samplerData>
              <xml>false</xml>
              <fieldNames>true</fieldNames>
              <responseHeaders>false</responseHeaders>
              <requestHeaders>false</requestHeaders>
              <responseDataOnError>false</responseDataOnError>
              <saveAssertionResultsFailureMessage>true</saveAssertionResultsFailureMessage>
              <assertionsResultsToSave>0</assertionsResultsToSave>
              <bytes>true</bytes>
              <sentBytes>true</sentBytes>
              <url>true</url>
              <threadCounts>true</threadCounts>
              <idleTime>true</idleTime>
              <connectTime>true</connectTime>
            </value>
          </objProp>
          <stringProp name="filename">docs/jmeter_benchmark_results.csv</stringProp>
        </ResultCollector>
        <hashTree/>
      </hashTree>
    </hashTree>
  </hashTree>
</jmeterTestPlan>'''
    jmx_path = "docs/ifrdss_jmeter_test_plan.jmx"
    with open(jmx_path, "w", encoding="utf-8") as f:
        f.write(jmx_content)
    print(f"[OK] Created Apache JMeter Test Plan: {jmx_path}")

def generate_csv_results(results):
    csv_path = "docs/jmeter_benchmark_results.csv"
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("Concurrency_Threads,Total_Samples,Avg_Latency_ms,Median_ms,P90_ms,P95_ms,P99_ms,Min_ms,Max_ms,Throughput_TPS,Bandwidth_KB_sec,Error_Percent\n")
        for c, v in results.items():
            f.write(f"{c},{v['samples']},{v['avg_ms']:.2f},{v['median_ms']:.2f},{v['p90_ms']:.2f},{v['p95_ms']:.2f},{v['p99_ms']:.2f},{v['min_ms']:.2f},{v['max_ms']:.2f},{v['tps']:.2f},{v['kb_sec']:.2f},{v['error_pct']:.2f}\n")
    print(f"[OK] Saved JMeter Summary CSV: {csv_path}")

if __name__ == "__main__":
    generate_jmeter_jmx()
    res = run_concurrency_test([1, 5, 10, 25, 50])
    ep_s = run_endpoint_breakdown()
    plot_charts(res, ep_s)
    generate_csv_results(res)
    print("\n[OK] JMeter Load Testing Suite Completed Successfully!")
