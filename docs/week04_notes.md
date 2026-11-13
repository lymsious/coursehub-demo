Trước khi tạo index:

- Scan type: Seq Scan on enrollment_events
- Execution Time: 4.731 ms

Sau khi tạo index:

- Scan type: Index Scan using idx_enrollment_events_dataset_student_time on enrollment_events
- Số dòng: trả về 50 dòng
- Số buffers: 53
- Execution Time: 0.080 ms
