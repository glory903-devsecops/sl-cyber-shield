<%@ page contentType="text/html; charset=UTF-8" %>
<%@ taglib prefix="s" uri="/struts-tags" %>
<html>
<head>
    <title>직원 정보 조회 · 얼굴 사진 업로드</title>
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
            --success: #10b981;
            --danger: #ef4444;
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
            max-width: 1100px;
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

        .grid {
            display: grid;
            grid-template-columns: 1fr 1.2fr;
            gap: 24px;
        }

        .card {
            background: var(--card);
            border-radius: 16px;
            padding: 24px;
            box-shadow: var(--shadow);
            border: 1px solid var(--border);
        }

        .card h2 {
            margin: 0 0 16px;
            font-size: 18px;
        }

        .hint {
            color: var(--muted);
            font-size: 13px;
            margin-top: 6px;
        }

        .upload-box {
            display: grid;
            gap: 16px;
        }

        .upload-field {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .upload-field input[type="file"] {
            padding: 12px;
            border: 1px dashed var(--border);
            border-radius: 12px;
            background: #f9fafb;
        }

        .btn {
            background: var(--accent);
            color: #fff;
            border: none;
            padding: 12px 18px;
            border-radius: 12px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s ease;
        }

        .btn:hover {
            background: var(--accent-strong);
        }

        .alert {
            padding: 12px 16px;
            border-radius: 12px;
            border: 1px solid var(--border);
            background: #f8fafc;
            font-size: 14px;
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

        .search {
            display: flex;
            gap: 12px;
            align-items: center;
            margin-bottom: 16px;
        }

        .search input {
            flex: 1;
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 10px 12px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        th, td {
            text-align: left;
            padding: 10px 8px;
            border-bottom: 1px solid var(--border);
            font-size: 14px;
        }

        th {
            font-weight: 600;
            color: var(--muted);
        }

        .status {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 10px;
            border-radius: 999px;
            font-size: 12px;
            background: #eef2ff;
            color: #4338ca;
        }

        .preview {
            display: flex;
            gap: 16px;
            align-items: center;
        }

        .preview img {
            width: 88px;
            height: 88px;
            object-fit: cover;
            border-radius: 16px;
            border: 1px solid var(--border);
            background: #fff;
        }

        @media (max-width: 900px) {
            .grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>

<body>
<div class="page">
    <header>
        <div class="title">
            <h1>직원 정보 조회 시스템</h1>
            <p>직원 기본 정보를 조회하고 얼굴 사진을 업로드합니다.</p>
        </div>
        <div class="status">운영 중</div>
    </header>

    <div class="grid">
        <section class="card">
            <h2>얼굴 사진 업로드</h2>
            <div class="upload-box">
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

                <s:form action="upload" method="post" enctype="multipart/form-data">
                    <div class="upload-field">
                        <label for="faceUpload">직원 얼굴 사진</label>
                        <input id="faceUpload" type="file" name="upload" accept="image/*" onchange="previewFace(event)" />
                        <span class="hint">JPG, PNG 등 이미지 파일만 업로드됩니다.</span>
                    </div>
                    <div class="preview">
                        <img id="previewImage" src="" alt="미리보기" style="display:none;" />
                        <div>
                            <div class="hint">미리보기는 브라우저에서만 표시됩니다.</div>
                            <div class="hint">업로드 후 파일은 서버에 저장됩니다.</div>
                        </div>
                    </div>
                    <div>
                        <button type="submit" class="btn">얼굴 사진 업로드</button>
                    </div>
                </s:form>
            </div>
        </section>

        <section class="card">
            <h2>직원 정보 조회</h2>
            <div class="search">
                <input id="employeeSearch" type="text" placeholder="이름, 부서, 직무로 검색" onkeyup="filterEmployees()" />
            </div>
            <table id="employeeTable">
                <thead>
                    <tr>
                        <th>사번</th>
                        <th>이름</th>
                        <th>부서</th>
                        <th>직무</th>
                        <th>상태</th>
                    </tr>
                </thead>
                <tbody>
                    <s:iterator value="employees">
                        <tr>
                            <td><s:property value="employeeCode"/></td>
                            <td><s:property value="name"/></td>
                            <td><s:property value="department"/></td>
                            <td><s:property value="role"/></td>
                            <td><span class="status"><s:property value="status"/></span></td>
                        </tr>
                    </s:iterator>
                </tbody>
            </table>
        </section>
    </div>
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

    function filterEmployees() {
        const keyword = document.getElementById("employeeSearch").value.toLowerCase();
        const rows = document.querySelectorAll("#employeeTable tbody tr");
        rows.forEach(row => {
            const text = row.innerText.toLowerCase();
            row.style.display = text.includes(keyword) ? "" : "none";
        });
    }
</script>
</body>
</html>
