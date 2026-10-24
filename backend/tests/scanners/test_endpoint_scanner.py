import pytest
from src.scanners.endpoints.scanner import scan_endpoints
from src.scanners.common.enums import AssetType, Language

def test_scan_python_fastapi_and_flask_routes():
    code = """
from fastapi import FastAPI, APIRouter
app = FastAPI()
router = APIRouter()

@app.get("/api/v1/users")
def get_users():
    return []

@router.post("/api/v1/items")
def create_item():
    pass

@app.route("/legacy")
def legacy():
    pass
"""
    findings = scan_endpoints("repo", "api.py", code, Language.PYTHON)
    assert len(findings) >= 3
    paths = [f.extra.get("path") for f in findings if f.extra]
    assert "/api/v1/users" in paths
    assert "/api/v1/items" in paths
    assert "/legacy" in paths
    methods = [f.extra.get("method") for f in findings if f.extra]
    assert "GET" in methods
    assert "POST" in methods

def test_scan_python_server_listener():
    code_public = """
import uvicorn
if __name__ == '__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=8080)
"""
    findings_pub = scan_endpoints("repo", "server.py", code_public, Language.PYTHON)
    assert len(findings_pub) >= 1
    assert findings_pub[0].extra.get("network_exposure") == "INTERNET_FACING"
    assert findings_pub[0].extra.get("port") == 8080

    code_internal = """
app.run(host="127.0.0.1", port=5000)
"""
    findings_int = scan_endpoints("repo", "internal.py", code_internal, Language.PYTHON)
    assert len(findings_int) >= 1
    assert findings_int[0].extra.get("network_exposure") == "INTERNAL"

def test_scan_python_http_client():
    code = """
import requests
resp = requests.get("https://api.example.com/data")
"""
    findings = scan_endpoints("repo", "client.py", code, Language.PYTHON)
    assert len(findings) >= 1
    assert findings[0].operation == "endpoint_client"
    assert "https://api.example.com/data" in findings[0].extra.get("url")
    assert findings[0].extra.get("network_exposure") == "INTERNET_FACING"

def test_scan_java_spring_endpoints():
    code = """
package com.example;
import org.springframework.web.bind.annotation.*;

@RestController
public class OrderController {
    @GetMapping("/orders")
    public List<Order> getOrders() { return null; }

    @PostMapping(value = "/orders/create")
    public void createOrder() {}
}
"""
    findings = scan_endpoints("repo", "OrderController.java", code, Language.JAVA)
    assert len(findings) >= 2
    paths = [f.extra.get("path") for f in findings if f.extra]
    assert "/orders" in paths
    assert "/orders/create" in paths

def test_scan_go_routes_and_server():
    code = """
package main
import (
    "net/http"
)
func main() {
    http.HandleFunc("/status", statusHandler)
    http.ListenAndServe(":8080", nil)
}
"""
    findings = scan_endpoints("repo", "main.go", code, Language.GO)
    assert len(findings) >= 2
    ops = [f.operation for f in findings]
    assert "endpoint_declaration" in ops
    assert "server_listener" in ops

def test_scan_endpoints_negative_clean_file():
    code = """
def calculate_sum(a, b):
    return a + b
"""
    findings = scan_endpoints("repo", "math.py", code, Language.PYTHON)
    assert len(findings) == 0
