import redis
from redis import asyncio as aioredis
from urllib.parse import urlparse
import asyncio
import sys


def parse_redis_service_url(redis_url):
    parsed_url = urlparse(redis_url)
    if parsed_url.scheme != "redis":
        raise ValueError("Invalid Redis URL scheme. Must be 'redis'.")
    return {
        "username": parsed_url.username or None,
        "password": parsed_url.password or None,
        "service": parsed_url.hostname or "mymaster",
        "port": parsed_url.port or 6379,
        "db": int(parsed_url.path.lstrip("/") or 0),
    }


def get_redis_connection(redis_url, redis_sentinels, decode_responses=True):
    if redis_sentinels:
        redis_config = parse_redis_service_url(redis_url)
        sentinel = redis.sentinel.Sentinel(
            redis_sentinels,
            port=redis_config["port"],
            db=redis_config["db"],
            username=redis_config["username"],
            password=redis_config["password"],
            decode_responses=decode_responses,
        )
        # Get a master connection from Sentinel
        return sentinel.master_for(redis_config["service"])
    else:
        # Standard Redis connection
        return redis.Redis.from_url(redis_url, decode_responses=decode_responses)


def test_redis_connection_sync(redis_url, redis_sentinels=None):
    """同步方式测试Redis连接"""
    print("=" * 50)
    print("开始测试Redis连接 (同步模式)")
    print("=" * 50)

    try:
        # 获取Redis连接
        r = get_redis_connection(redis_url, redis_sentinels)
        print(f"✓ Redis连接对象创建成功")

        # 测试ping
        response = r.ping()
        print(f"✓ Ping测试成功: {response}")

        # 测试基本操作
        test_key = "test_connection_key"
        test_value = "Hello Redis!"

        # 设置值
        r.set(test_key, test_value)
        print(f"✓ 设置键值对成功: {test_key} = {test_value}")

        # 获取值
        retrieved_value = r.get(test_key)
        print(f"✓ 获取值成功: {retrieved_value}")

        # 验证值是否正确
        if retrieved_value == test_value:
            print("✓ 数据一致性验证通过")
        else:
            print(f"✗ 数据不一致: 期望 {test_value}, 实际 {retrieved_value}")

        # 删除测试键
        r.delete(test_key)
        print("✓ 清理测试数据完成")

        # 获取Redis信息
        info = r.info()
        print(f"✓ Redis版本: {info.get('redis_version', 'Unknown')}")
        print(f"✓ 连接的数据库: {info.get('db0', {}).get('keys', 0)} 个键")

        print("\n🎉 Redis连接测试完全成功!")
        return True

    except redis.ConnectionError as e:
        print(f"✗ Redis连接错误: {e}")
        return False
    except redis.AuthenticationError as e:
        print(f"✗ Redis认证错误: {e}")
        return False
    except Exception as e:
        print(f"✗ 其他错误: {e}")
        return False


async def test_redis_connection_async(redis_url, redis_sentinels=None):
    """异步方式测试Redis连接"""
    print("=" * 50)
    print("开始测试Redis连接 (异步模式)")
    print("=" * 50)

    try:
        # 创建异步Redis连接
        if redis_sentinels:
            # 如果使用Sentinel，需要特殊处理
            redis_config = parse_redis_service_url(redis_url)
            r = aioredis.Redis(
                host=redis_config["service"],
                port=redis_config["port"],
                db=redis_config["db"],
                username=redis_config["username"],
                password=redis_config["password"],
                decode_responses=True,
            )
        else:
            r = aioredis.from_url(redis_url, decode_responses=True)

        print(f"✓ 异步Redis连接对象创建成功")

        # 测试ping
        response = await r.ping()
        print(f"✓ 异步Ping测试成功: {response}")

        # 测试基本操作
        test_key = "test_async_connection_key"
        test_value = "Hello Async Redis!"

        # 设置值
        await r.set(test_key, test_value)
        print(f"✓ 异步设置键值对成功: {test_key} = {test_value}")

        # 获取值
        retrieved_value = await r.get(test_key)
        print(f"✓ 异步获取值成功: {retrieved_value}")

        # 验证值是否正确
        if retrieved_value == test_value:
            print("✓ 异步数据一致性验证通过")
        else:
            print(f"✗ 异步数据不一致: 期望 {test_value}, 实际 {retrieved_value}")

        # 删除测试键
        await r.delete(test_key)
        print("✓ 异步清理测试数据完成")

        # 关闭连接
        await r.close()
        print("✓ 异步连接已关闭")

        print("\n🎉 异步Redis连接测试完全成功!")
        return True

    except Exception as e:
        print(f"✗ 异步测试错误: {e}")
        return False


def main():
    # 配置你的Redis连接信息
    # 示例配置 - 请根据你的实际情况修改
    redis_url = "redis://192.168.200.165:6379/0"  # 修改为你的Redis URL
    redis_sentinels = (
        None  # 如果使用Sentinel，设置为 [('host1', 26379), ('host2', 26379)]
    )

    print("Redis连接测试工具")
    print("请确保已修改redis_url变量为你的实际Redis连接地址")
    print()

    # 同步测试
    sync_success = test_redis_connection_sync(redis_url, redis_sentinels)

    print()

    # 异步测试
    async_success = asyncio.run(test_redis_connection_async(redis_url, redis_sentinels))

    # 总结
    print("\n" + "=" * 50)
    print("测试结果总结:")
    print(f"同步连接测试: {'✓ 成功' if sync_success else '✗ 失败'}")
    print(f"异步连接测试: {'✓ 成功' if async_success else '✗ 失败'}")

    if sync_success and async_success:
        print("🎉 所有测试通过，Redis连接正常!")
        sys.exit(0)
    else:
        print("❌ 部分测试失败，请检查Redis配置")
        sys.exit(1)


if __name__ == "__main__":
    main()
