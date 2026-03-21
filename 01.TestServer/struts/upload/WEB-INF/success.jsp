<%@ page contentType="text/html;charset=UTF-8" language="java" %>
<%@ taglib prefix="s" uri="/struts-tags" %>
<html>
<head>
  <title>얼굴 사진 업로드 완료</title>
  <style>
      body {
          margin: 0;
          font-family: "Segoe UI", "Noto Sans KR", sans-serif;
          background: #f5f7fb;
          color: #1f2a44;
      }
      .page {
          max-width: 720px;
          margin: 0 auto;
          padding: 64px 24px;
      }
      .card {
          background: #ffffff;
          border-radius: 16px;
          padding: 28px;
          box-shadow: 0 18px 45px rgba(15, 23, 42, 0.08);
          border: 1px solid #e5e7eb;
      }
      h2 {
          margin: 0 0 12px;
      }
      .meta {
          background: rgba(16, 185, 129, 0.1);
          border: 1px solid rgba(16, 185, 129, 0.3);
          color: #065f46;
          padding: 12px 16px;
          border-radius: 12px;
          margin-bottom: 16px;
          font-size: 14px;
      }
      .detail {
          font-size: 14px;
          color: #4b5563;
          margin-bottom: 8px;
      }
      a.button {
          display: inline-flex;
          padding: 10px 16px;
          border-radius: 12px;
          background: #3b82f6;
          color: #fff;
          text-decoration: none;
          font-weight: 600;
      }
  </style>
</head>
<body>
<div class="page">
  <div class="card">
    <h2>얼굴 사진 업로드 완료</h2>

    <s:if test="hasActionMessages()">
        <div class="meta">
            <s:iterator value="actionMessages">
                <div><s:property /></div>
            </s:iterator>
        </div>
    </s:if>

    <div class="detail">저장된 파일: <s:property value="savedFileName"/></div>
    <div class="detail">저장 경로: <s:property value="savedFilePath"/></div>

    <s:url var="uploadActionUrl" action="upload"/>
    <a class="button" href="<s:property value='#uploadActionUrl'/>">업로드 페이지로 돌아가기</a>
  </div>
</div>
</body>
</html>
