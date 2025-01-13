# EXPLAIN

***EXPLAIN是優化MySQL查詢的關鍵技能。它能幫助我們理解資料庫如何執行查詢，從而找出潛在的性能問題.***

### 使用 EXPLAIN

在 SELECT、UPDATE、DELETE 或 INSERT 語句前加上 EXPLAIN 關鍵字：

```sql
EXPLAIN SELECT * FROM users WHERE status = 'active';
```

### 關鍵列解釋

#### 1. id

* 選擇標識符
* 數字越大越先執行
* 相同的話，從上往下執行

#### 2. select\_type

* SIMPLE: 簡單查詢（非子查詢或 UNION）
* PRIMARY: 最外層查詢
* SUBQUERY: 子查詢
* DERIVED: 衍生表（FROM 子句中的子查詢）
* UNION: UNION 中第二個及後面的查詢
* UNION RESULT: UNION 的結果

#### 3. table

* 查詢涉及的表名

#### 4. type（重要，按性能從好到壞排序）

* system: 表只有一行記錄
* const: 最多只有一行匹配，用於主鍵或唯一索引查詢
* eq\_ref: 對於每個索引鍵，表中只有一條記錄與之匹配
* ref: 非唯一性索引掃描
* range: 索引範圍掃描
* index: 全索引掃描
* ALL: 全表掃描（最差）

#### 5. possible\_keys

* 可能用到的索引

#### 6. key

* 實際使用的索引

#### 7. key\_len

* 使用的索引長度

#### 8. ref

* 顯示哪些列或常量被用於查找索引列上的值

#### 9. rows

* 預計要檢查的行數

#### 10. Extra（包含額外信息）

* Using index: 查詢使用了覆蓋索引
* Using where: 使用 WHERE 條件過濾結果
* Using temporary: 使用臨時表
* Using filesort: 需要額外的排序操作
* Using join buffer: 使用連接緩衝

### 解讀技巧

1. 關注 type 列，盡量避免出現 ALL（全表掃描）
2. 檢查 possible\_keys 和 key，確保正確的索引被使用
3. 留意 rows，這表示預計掃描的行數，越少越好
4. 注意 Extra 列中的警告信息，如 Using filesort 或 Using temporary

### 優化方向

* 如果 type 是 ALL，考慮添加適當的索引
* 如果 key 為 NULL，檢查索引設計或查詢條件
* 如果 rows 很大，考慮優化查詢或索引
* 如果出現 Using filesort 或 Using temporary，考慮優化排序或分組操作

### 補充說明和實際應用的建議：

1.  EXPLAIN FORMAT=JSON 使用 JSON 格式可以獲得更詳細的執行計劃信息：

    ```sql
    EXPLAIN FORMAT=JSON SELECT * FROM users WHERE status = 'active';
    ```

    這會提供更多細節，如成本估算、緩衝區使用情況等。
2.  實際案例分析 假設我們有這樣一個查詢：

    ```sql
    EXPLAIN SELECT u.name, o.order_date
    FROM users u JOIN orders o ON u.id = o.user_id
    WHERE u.status = 'active' AND o.order_date > '2023-01-01';
    ```

    我們應該關注：

    * JOIN 操作的 type（希望看到 **eq\_ref** 或 **ref**）
    * 是否使用了適當的索引（檢查 key 列）
    * rows 估算是否合理
3.  優化器提示 有時可以使用優化器提示來影響執行計劃：

    ```sql
    EXPLAIN SELECT /*+ INDEX(users idx_status) */ *
    FROM users WHERE status = 'active';
    ```
4. 子查詢優化 對於包含子查詢的語句，特別關注 **select\_type**，看是否可以重寫為 JOIN 來提高性能。
5. 臨時表和文件排序 如果看到 "**Using temporary**" 和 "**Using filesort**"，考慮添加適當的索引或重寫查詢。
6. 索引使用情況 比較 **possible\_keys** 和 **key**，如果 **possible\_keys** 有列出但 **key** 為 **NULL**，可能需要強制使用索引或重新評估索引設計。
7. 連接查詢優化 對於多表連接，確保連接條件上有適當的索引，並且連接順序是最優的。
8. 定期分析 使用 `ANALYZE TABLE` 來更新統計信息，確保優化器使用最新的資料來生成執行計劃。
9. 結合慢查詢日誌 將 `EXPLAIN` 的結果與慢查詢日誌結合分析，找出需要優化的查詢。