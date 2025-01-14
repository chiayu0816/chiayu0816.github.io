---
title: "context"
categories: ["Go"]
---

**用於在 goroutine 之間傳遞截止日期、取消信號和其他請求範圍的值。以下是 context 的主要特點和用途：**

* 取消操作： context 允許你取消長時間運行的操作。當一個操作被取消時，使用該 context 的所有 goroutine 都應該立即停止工作並返回。
* 截止時間： 你可以為 context 設置一個截止時間，當到達該時間時，使用此 context 的所有操作都應該結束。
* 值傳遞： context 可以攜帶請求範圍的值，這些值可以在整個調用鏈中傳遞。
* 層級結構： context 可以形成一個樹狀結構，子 context 可以從父 context 派生，形成一個層級關係。

**Context 有兩個主要的功能：**

* 通知子協程退出 (正常退出，超時退出等)
* 傳遞必要的參數。

範例：

```go
package test

import (
	"context"
	"fmt"
	"testing"
	"time"
)

type Options struct{ Interval time.Duration }

func reqTask(ctx context.Context, name string) {
	for {
		select {
		case <-ctx.Done():
			fmt.Println("stop", name, ctx.Err())
			return
		default:
			fmt.Println(name, "send request")
			time.Sleep(1 * time.Second)
		}
	}
}

func reqTaskWithValue(ctx context.Context, name string) {
	for {
		select {
		case <-ctx.Done():
			fmt.Println("stop", name, ctx.Err())
			return
		default:
			fmt.Println(name, "send request")
			op := ctx.Value("options").(*Options)
			time.Sleep(op.Interval * time.Second)
		}
	}
}

func TestContextWithCancel(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	go reqTask(ctx, "worker1")
	time.Sleep(3 * time.Second)
	cancel()
	time.Sleep(3 * time.Second)
}

func TestContextWithCancelByMultiGotoutine(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())

	go reqTask(ctx, "worker1")
	go reqTask(ctx, "worker2")

	time.Sleep(3 * time.Second)
	cancel()
	time.Sleep(3 * time.Second)
}

func TestContextWithCancelIncludeValue(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	vCtx := context.WithValue(ctx, "options", &Options{1})

	go reqTaskWithValue(vCtx, "worker1")
	go reqTaskWithValue(vCtx, "worker2")

	time.Sleep(3 * time.Second)
	cancel()
	time.Sleep(3 * time.Second)
}

func TestContextWithTimeout(t *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	go reqTask(ctx, "worker1")
	go reqTask(ctx, "worker2")
	time.Sleep(3 * time.Second)
	fmt.Println("before cancel")
	cancel()
	time.Sleep(3 * time.Second)
}

func TestContextWithDeadline(t *testing.T) {
	ctx, cancel := context.WithDeadline(context.Background(), time.Now().Add(1*time.Second))
	go reqTask(ctx, "worker1")
	go reqTask(ctx, "worker2")
	time.Sleep(3 * time.Second)
	fmt.Println("before cancel")
	cancel()
	time.Sleep(3 * time.Second)
}

```