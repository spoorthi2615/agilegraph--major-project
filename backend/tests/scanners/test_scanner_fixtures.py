import pytest
from src.scanners.python.scanner import scan_python_code
from src.scanners.java.scanner import scan_java_code
from src.scanners.go.scanner import scan_go_code

def test_python_scanner_coverage():
    code = """
import hashlib
from Crypto.Cipher import DES
from hashlib import sha1
import rsa
import hashlib as h
import Cryptodome.Cipher.AES
from cryptography.hazmat.primitives.asymmetric.rsa import generate_private_key

def hash_data():
    h1 = hashlib.md5()
    h2 = hashlib.new("sha1")
    h3 = sha1(b"test")
    h4 = h.sha256()
    return h1, h2, h3, h4

def encrypt_data():
    cipher = DES.new(b'12345678', DES.MODE_ECB)
    cipher2 = Cryptodome.Cipher.AES.new()
    
def gen_key():
    private_key = rsa.generate_private_key(65537, 1024)
    pk2 = generate_private_key(key_size=2048)
    pk3 = rsa.newkeys(512)
"""
    findings = scan_python_code("test", "test.py", code)
    
    algorithms = [f.algorithm.lower() for f in findings if f.algorithm]
    
    assert "md5" in algorithms
    assert "sha1" in algorithms
    assert "des" in algorithms
    assert "aes" in algorithms
    assert "rsa" in algorithms
    assert "sha256" in algorithms
    
    key_sizes = [f.extra.get("key_size") for f in findings if f.extra and "key_size" in f.extra]
    assert 1024 in key_sizes
    assert 2048 in key_sizes
    assert 512 in key_sizes

def test_java_scanner_coverage():
    code = """
import javax.crypto.Cipher;
import java.security.MessageDigest;
import java.security.KeyPairGenerator;

public class Test {
    public void test() throws Exception {
        MessageDigest md = MessageDigest.getInstance("MD5");
        MessageDigest sha = MessageDigest.getInstance("SHA-1");
        Cipher cipher = Cipher.getInstance("DES/ECB/PKCS5Padding");
        
        KeyPairGenerator keyGen = KeyPairGenerator.getInstance("RSA");
        keyGen.initialize(1024);
        
        // false positive check
        SomeClass obj = new SomeClass();
        obj.initialize(512); // should not be associated with RSA
    }
}
"""
    findings = scan_java_code("test", "Test.java", code)
    algorithms = [f.algorithm.lower() for f in findings if f.algorithm]
    
    # We should have md5, sha-1, des/ecb/pkcs5padding, rsa, and rsa with keysize 1024
    assert "md5" in algorithms
    assert "sha-1" in algorithms
    assert "des/ecb/pkcs5padding" in algorithms
    
    key_sizes = [f.extra.get("key_size") for f in findings if f.extra and "key_size" in f.extra]
    assert 1024 in key_sizes
    assert 512 not in key_sizes

def test_go_scanner_coverage():
    code = """
package main

import (
    "crypto/md5"
    "crypto/sha1"
    "crypto/des"
    "crypto/rsa"
    "crypto/rand"
)

func main() {
    md5.New()
    sha1.New()
    des.NewCipher([]byte("12345678"))
    
    privateKey, _ := rsa.GenerateKey(rand.Reader, 1024)
}
"""
    findings = scan_go_code("test", "main.go", code)
    algorithms = [f.algorithm.lower() for f in findings if f.algorithm]
    
    assert "md5" in algorithms
    assert "sha1" in algorithms
    assert "des" in algorithms
    assert "rsa" in algorithms
    
    key_sizes = [f.extra.get("key_size") for f in findings if f.extra and "key_size" in f.extra]
    assert 1024 in key_sizes
