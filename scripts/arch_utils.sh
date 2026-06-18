#!/bin/bash

normalize_arch_to_kernel() {
    local arch="$1"
    case "${arch}" in
        arm64|aarch64)
            echo "aarch64"
            ;;
        amd64|x86_64)
            echo "x86_64"
            ;;
        *)
            echo "${arch}"
            ;;
    esac
}

normalize_arch_to_debian() {
    local arch="$1"
    case "${arch}" in
        arm64|aarch64)
            echo "arm64"
            ;;
        amd64|x86_64)
            echo "amd64"
            ;;
        *)
            echo "${arch}"
            ;;
    esac
}

validate_arch() {
    local arch="$1"
    case "${arch}" in
        arm64|aarch64|amd64|x86_64)
            return 0
            ;;
        *)
            echo "错误: 不支持的架构 '${arch}'，支持的架构: arm64, aarch64, amd64, x86_64" >&2
            return 1
            ;;
    esac
}