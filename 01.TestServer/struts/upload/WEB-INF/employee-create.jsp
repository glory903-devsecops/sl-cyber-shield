<%@ page contentType="text/html; charset=UTF-8" %>
<%@ taglib prefix="s" uri="/struts-tags" %>
<html>
<head>
    <title>직원 등록</title>
    <style>
        :root {
            color-scheme: light;
            --bg: #f5f7fb;
            --card: #ffffff;
            --text: #1f2a44;
            --muted: #6b7280;
            --accent: #3b82f6;
            --accent-strong: #1d4ed8;
            --border: #e5e7eb;
            --shadow: 0 18px 45px rgba(15, 23, 42, 0.08);
        }

        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            font-family: "Segoe UI", "Noto Sans KR", sans-serif;
            background: var(--bg);
            color: var(--text);
        }

        .page {
            max-width: 900px;
            margin: 0 auto;
            padding: 48px 24px 80px;
        }

        header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 24px;
            margin-bottom: 32px;
        }

        .title h1 {
            margin: 0 0 8px;
            font-size: 28px;
            font-weight: 700;
        }

        .title p {
            margin: 0;
            color: var(--muted);
        }

        .actions {
            display: flex;
            gap: 12px;
        }

        .btn {
            background: var(--accent);
            color: #fff;
            border: none;
            padding: 10px 16px;
            border-radius: 12px;
            font-weight: 600;
            text-decoration: none;
        }

        .btn.secondary {
            background: #e0e7ff;
            color: #3730a3;
        }

        .card {
            background: var(--card);
            border-radius: 16px;
            padding: 24px;
            box-shadow: var(--shadow);
            border: 1px solid var(--border);
        }

        .field {
            display: flex;
            flex-direction: column;
            gap: 8px;
            margin-bottom: 16px;
        }

        .field input,
        .field select {
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 10px 12px;
        }

        .upload-field input[type="file"] {
            padding: 12px;
            border: 1px dashed var(--border);
            border-radius: 12px;
            background: #f9fafb;
        }

        .preview {
            display: flex;
            gap: 16px;
            align-items: center;
            margin-bottom: 16px;
        }

        .preview img {
            width: 96px;
            height: 96px;
            object-fit: cover;
            border-radius: 16px;
            border: 1px solid var(--border);
            background: #fff;
        }

        .alert {
            padding: 12px 16px;
            border-radius: 12px;
            border: 1px solid var(--border);
            background: #f8fafc;
            font-size: 14px;
            margin-bottom: 16px;
        }

        .alert.success {
            border-color: rgba(16, 185, 129, 0.3);
            background: rgba(16, 185, 129, 0.1);
            color: #065f46;
        }

        .alert.error {
            border-color: rgba(239, 68, 68, 0.3);
            background: rgba(239, 68, 68, 0.1);
            color: #991b1b;
        }
    </style>
</head>
<body>
<div class="page">
    <header>
        <div class="title">
            <h1>직원 등록</h1>
            <p>직원 정보와 얼굴 사진을 함께 등록합니다.</p>
        </div>
        <div class="actions">
            <s:url var="listUrl" action="employees" />
            <s:url var="createUrl" action="employee-create" />
            <a class="btn secondary" href="<s:property value='#listUrl' />">직원 목록</a>
            <a class="btn" href="<s:property value='#createUrl' />">직원 등록</a>
        </div>
    </header>

    <section class="card">
        <s:if test="hasActionMessages()">
            <div class="alert success">
                <s:iterator value="actionMessages">
                    <div><s:property /></div>
                </s:iterator>
            </div>
        </s:if>

        <s:if test="hasActionErrors()">
            <div class="alert error">
                <s:iterator value="actionErrors">
                    <div><s:property /></div>
                </s:iterator>
            </div>
        </s:if>

        <s:form action="employee-create" method="post" enctype="multipart/form-data">
            <div class="field">
                <label>사번</label>
                <input type="text" name="employeeCode" placeholder="EMP-1001" />
            </div>
            <div class="field">
                <label>이름</label>
                <input type="text" name="name" placeholder="홍길동" />
            </div>
            <div class="field">
                <label>부서</label>
                <input type="text" name="department" placeholder="개발팀" />
            </div>
            <div class="field">
                <label>직무</label>
                <input type="text" name="role" placeholder="백엔드 엔지니어" />
            </div>
            <div class="field">
                <label>상태</label>
                <select name="status">
                    <option value="">선택해주세요</option>
                    <option value="재직">재직</option>
                    <option value="휴직">휴직</option>
                    <option value="퇴사">퇴사</option>
                </select>
            </div>
            <div class="field upload-field">
                <label>얼굴 사진</label>
                <input id="faceUpload" type="file" name="upload" accept="image/*" onchange="previewFace(event)" />
            </div>
            <div class="preview">
                <img id="previewImage" src="" alt="미리보기" style="display:none;" />
                <div>
                    <div class="hint">미리보기는 브라우저에서만 표시됩니다.</div>
                </div>
            </div>
            <button type="submit" class="btn">직원 등록</button>
        </s:form>
    </section>
</div>

<script>
    function previewFace(event) {
        const file = event.target.files && event.target.files[0];
        const preview = document.getElementById("previewImage");
        if (!file) {
            preview.src = "";
            preview.style.display = "none";
            return;
        }
        preview.src = URL.createObjectURL(file);
        preview.style.display = "block";
    }
</script>
</body>
</html>
