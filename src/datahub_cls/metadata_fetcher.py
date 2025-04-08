#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Datahub에서 테이블 및 컬럼 설명을 가져오는
예시 스크립트입니다.
"""

import os
import json
import pandas as pd
from datahub.metadata.schema_classes import (
    DatasetPropertiesClass,
    SchemaMetadataClass,
)
from datahub.emitter.rest_emitter import DatahubRestEmitter
import requests


class DatahubMetadataFetcher:
    def __init__(self, gms_server="http://localhost:8080", extra_headers={}):
        # gms_server 주소 유효성 검사
        if not self._is_valid_gms_server(gms_server):
            raise ValueError(f"유효하지 않은 GMS 서버 주소: {gms_server}")

        self.emitter = DatahubRestEmitter(
            gms_server=gms_server, extra_headers=extra_headers
        )
        self.datahub_graph = self.emitter.to_graph()

    def _is_valid_gms_server(self, gms_server):
        # GMS 서버 주소의 유효성을 검사하는 로직 추가
        # GraphQL 요청을 사용하여 서버 상태 확인
        query = {"query": "{ health { status } }"}
        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(
                f"{gms_server}/api/graphql", json=query, headers=headers
            )
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def get_urns(self):
        # 필터를 적용하여 데이터셋의 URN 가져오기
        return self.datahub_graph.get_urns_by_filter()

    def get_table_name(self, urn):
        # URN에 대한 테이블 이름 가져오기
        dataset_properties = self.datahub_graph.get_aspect(
            urn, aspect_type=DatasetPropertiesClass
        )
        if dataset_properties:
            return dataset_properties.get("name", None)
        return None

    def get_table_description(self, urn):
        # URN에 대한 테이블 설명 가져오기
        dataset_properties = self.datahub_graph.get_aspect(
            urn, aspect_type=DatasetPropertiesClass
        )
        if dataset_properties:
            return dataset_properties.get("description", None)
        return None

    def get_column_names_and_descriptions(self, urn):
        # URN에 대한 컬럼 이름 및 설명 가져오기
        schema_metadata = self.datahub_graph.get_aspect(
            urn, aspect_type=SchemaMetadataClass
        )
        columns = []
        if schema_metadata:
            for field in schema_metadata.fields:
                columns.append(
                    {
                        "column_name": field.fieldPath,
                        "column_description": field.description,
                    }
                )
        return columns


def get_all_tables_info(fetcher):
    """모든 테이블의 이름과 설명을 가져오는 함수"""
    urns = fetcher.get_urns()
    table_info = []

    for urn in urns:
        table_name = fetcher.get_table_name(urn)
        table_description = fetcher.get_table_description(urn)
        if table_name:
            table_info.append(
                {
                    "urn": urn,
                    "table_name": table_name,
                    "table_description": table_description or "",
                }
            )

    return pd.DataFrame(table_info)


def get_columns_for_table(fetcher, table_name):
    """지정된 테이블의 모든 컬럼 정보를 가져오는 함수"""
    urns = fetcher.get_urns()

    for urn in urns:
        if fetcher.get_table_name(urn) == table_name:
            column_info = fetcher.get_column_names_and_descriptions(urn)
            return pd.DataFrame(column_info)

    print(f"❌ 테이블 '{table_name}'을(를) 찾을 수 없습니다.")
    return pd.DataFrame()


def search_tables(tables_df, keyword):
    """키워드를 포함하는 테이블을 검색하는 함수"""
    if tables_df.empty:
        print("❌ 테이블 정보가 로드되지 않았습니다.")
        return pd.DataFrame()

    # 테이블 이름이나 설명에 키워드가 포함된 테이블 검색
    result = tables_df[
        tables_df["table_name"].str.contains(keyword, case=False, na=False)
        | tables_df["table_description"].str.contains(keyword, case=False, na=False)
    ]

    return result


def get_complete_table_metadata(fetcher, table_name):
    """테이블의 모든 메타데이터(테이블 정보와 컬럼 정보)를 가져오는 함수"""
    urns = fetcher.get_urns()

    for urn in urns:
        if fetcher.get_table_name(urn) == table_name:
            # 테이블 정보 가져오기
            table_info = {
                "urn": urn,
                "table_name": table_name,
                "table_description": fetcher.get_table_description(urn) or "",
            }

            # 컬럼 정보 가져오기
            columns = fetcher.get_column_names_and_descriptions(urn)

            return {"table_info": table_info, "columns": columns}

    print(f"❌ 테이블 '{table_name}'을(를) 찾을 수 없습니다.")
    return None


def save_tables_to_csv(tables_df, filename="datahub_tables.csv"):
    """테이블 정보를 CSV 파일로 저장"""
    if tables_df.empty:
        print("❌ 저장할 테이블 정보가 없습니다.")
        return

    tables_df.to_csv(filename, index=False, encoding="utf-8")
    print(f"✅ 테이블 정보가 '{filename}'에 저장되었습니다.")


def save_all_metadata_to_json(fetcher, tables_df, filename="datahub_metadata.json"):
    """모든 테이블의 컬럼 정보를 JSON 파일로 저장"""
    if tables_df.empty:
        print("❌ 저장할 테이블 정보가 없습니다.")
        return

    all_metadata = {}
    for _, row in tables_df.iterrows():
        table_name = row["table_name"]
        metadata = get_complete_table_metadata(fetcher, table_name)
        if metadata:
            all_metadata[table_name] = metadata

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(all_metadata, f, ensure_ascii=False, indent=2)

    print(f"✅ 모든 메타데이터가 '{filename}'에 저장되었습니다.")


def main():
    """메인 함수"""
    # Datahub 서버 URL 설정 (환경 변수에서 가져오거나 직접 입력)
    # 환경 변수가 설정되어 있지 않으면 기본값 사용
    DATAHUB_SERVER = os.getenv("DATAHUB_SERVER", "http://localhost:8080")

    # API 키 또는 인증 정보가 필요한 경우 추가 헤더 설정
    # 예: extra_headers = {"Authorization": f"Bearer {os.getenv('DATAHUB_TOKEN')}"}
    extra_headers = {}

    try:
        # DatahubMetadataFetcher 인스턴스 생성
        fetcher = DatahubMetadataFetcher(
            gms_server=DATAHUB_SERVER, extra_headers=extra_headers
        )
        print(f"✅ Datahub 서버 ({DATAHUB_SERVER})에 성공적으로 연결됨")

        # 모든 테이블 정보 가져오기
        tables_df = get_all_tables_info(fetcher)
        print(f"✅ {len(tables_df)} 개의 테이블 정보를 가져왔습니다.")

        # 테이블 정보 출력
        if not tables_df.empty:
            print("\n테이블 목록 (처음 5개):")
            print(tables_df.head())

            # 첫 번째 테이블의 컬럼 정보 가져오기
            sample_table = tables_df.iloc[0]["table_name"]
            print(f"\n'{sample_table}' 테이블의 컬럼 정보:")
            columns_df = get_columns_for_table(fetcher, sample_table)
            print(columns_df)

            # 키워드로 테이블 검색 (예: 'user' 키워드 검색)
            search_keyword = "user"
            search_results = search_tables(tables_df, search_keyword)
            print(
                f"\n'{search_keyword}' 키워드 검색 결과: {len(search_results)}개 테이블 찾음"
            )

            if not search_results.empty:
                # 검색된 첫 번째 테이블의
                searched_table = search_results.iloc[0]["table_name"]
                metadata = get_complete_table_metadata(fetcher, searched_table)

                if metadata:
                    print(
                        f"\n테이블 정보: {metadata['table_info']['table_name']} - {metadata['table_info']['table_description']}"
                    )
                    print("\n컬럼 정보:")
                    for column in metadata["columns"][:5]:  # 처음 5개 컬럼만 표시
                        print(
                            f"- {column['column_name']}: {column['column_description'] or '설명 없음'}"
                        )

                    # 전체 컬럼 수 표시
                    if len(metadata["columns"]) > 5:
                        print(f"... 외 {len(metadata['columns']) - 5}개 컬럼")

            # 데이터 저장 예시
            save_tables_to_csv(tables_df)

            # 모든 메타데이터 저장 (주의: 테이블이 많을 경우 시간이 오래 걸릴 수 있음)
            # 아래 라인의 주석을 제거하면 모든 메타데이터를 JSON 파일로 저장
            # save_all_metadata_to_json(fetcher, tables_df)

    except ValueError as e:
        print(f"❌ 오류: {str(e)}")
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {str(e)}")


if __name__ == "__main__":
    main()
