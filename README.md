# MINDLE MODEL SCOUT

Hugging Face 기반 AI Model Scout Agent

## Mission
사용자가 필요한 AI 기능을 입력하면 Hugging Face에서 적합한 모델 후보를 탐색하고,
조사 · 분류 · 평가 · 추천하여 MINDLE 기준의 최적 후보를 제시한다.

## Core Flow
Requirement
→ Hugging Face Search
→ Candidate Collection
→ Metadata Normalization
→ License Gate
→ Scoring
→ Ranking
→ Recommendation
→ Model Card
→ Scout Report

## Development Principle
- Hugging Face 전담 독립 제품으로 우선 완성한다.
- 다른 MINDLE 시스템과의 통합은 이후 단계에서 진행한다.
- 기존 SSOT와 승인사항을 최우선 기준으로 유지한다.
- 검색 → 조사 → 분류 → 평가 → 추천의 핵심 흐름을 먼저 완성한다.

## Current Phase
PHASE 1 — Scout MVP

## First Gate
SCOUT-GATE-01

자연어 요구 입력
→ 실제 Hugging Face 후보 검색
→ Metadata 수집
→ License 판정
→ 100점 평가
→ Ranking
→ 추천
→ Model Card 출력

## Command Structure
신작가님
→ 아키 사령관
→ MODEL SCOUT 개발 및 검수
