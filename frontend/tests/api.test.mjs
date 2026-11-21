import assert from "node:assert/strict";
import test from "node:test";
import { api } from "../src/api.js";

test("1 - GET thanh cong tra ve du lieu JSON", async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () =>
    new Response(JSON.stringify([{ class_id: "WEB-01" }]), { status: 200 });
  try {
    const data = await api("/sections");
    assert.deepEqual(data, [{ class_id: "WEB-01" }]);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("2 - AbortError duoc giu nguyen khi request bi huy", async () => {
  const originalFetch = globalThis.fetch;
  const abortError = new DOMException(
    "The operation was aborted.",
    "AbortError",
  );
  globalThis.fetch = async () => {
    throw abortError;
  };
  try {
    await assert.rejects(
      () => api("/sections"),
      (err) => err === abortError,
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("3 - Loi mang/CORS nem thong bao ro rang", async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => {
    throw new TypeError("Failed to fetch");
  };
  try {
    await assert.rejects(
      () => api("/sections"),
      /Không nhận được phản hồi API/,
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("4 - DELETE thanh cong status 204 tra ve null", async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => new Response(null, { status: 204 });
  try {
    const data = await api("/enrollments/22000004/WEB-01", {
      method: "DELETE",
    });
    assert.equal(data, null);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("5 - Phan hoi khong phai JSON nem loi ro rang", async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => new Response("Bad Gateway", { status: 502 });
  try {
    await assert.rejects(
      () => api("/sections"),
      /HTTP 502: phản hồi không phải JSON\./,
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("6 - HTTP loi voi detail dang chuoi", async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () =>
    new Response(JSON.stringify({ detail: "Lop hoc phan da het cho" }), {
      status: 409,
    });
  try {
    await assert.rejects(
      () => api("/enrollments"),
      (err) =>
        err.status === 409 &&
        err.message === "HTTP 409: Lop hoc phan da het cho",
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("7 - HTTP loi 422 voi detail la danh sach item.msg", async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () =>
    new Response(
      JSON.stringify({
        detail: [{ msg: "Field required" }, { msg: "Invalid value" }],
      }),
      { status: 422 },
    );
  try {
    await assert.rejects(
      () => api("/enrollments"),
      (err) =>
        err.status === 422 &&
        err.message === "HTTP 422: Field required; Invalid value",
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("8 - POST kem body duoc JSON.stringify va co Content-Type", async () => {
  const originalFetch = globalThis.fetch;
  let capturedOptions;
  globalThis.fetch = async (_url, options) => {
    capturedOptions = options;
    return new Response(JSON.stringify({ message: "Dang ky thanh cong" }), {
      status: 201,
    });
  };
  try {
    const payload = { student_id: "22000004", class_section_id: "WEB-01" };
    await api("/enrollments", { method: "POST", body: payload });
    assert.equal(capturedOptions.method, "POST");
    assert.equal(capturedOptions.headers["Content-Type"], "application/json");
    assert.equal(capturedOptions.body, JSON.stringify(payload));
  } finally {
    globalThis.fetch = originalFetch;
  }
});
