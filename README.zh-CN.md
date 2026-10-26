# Satochip-25519-Applet (中文文档)

[![JavaCard](https://img.shields.io/badge/JavaCard-3.0.4%2B-blue.svg)](https://www.oracle.com/java/technologies/javacard.html)
[![Target](https://img.shields.io/badge/Target-NXP%20J3R452%20(P71D600)-green.svg)](https://www.nxp.com)
[![License](https://img.shields.io/badge/License-LGPL--3.0-orange.svg)](LICENSE)
[![Reproducible Build](https://img.shields.io/badge/Build-Reproducible%20(Verified)-brightgreen.svg)](dist/build-manifest.json)

> **专为 NXP JCOP 4.5 / J3R452 智能卡打造的原生硬件加速 Curve25519 (Ed25519 / X25519 / SLIP-0010) JavaCard Applet。**  
>
> 🌐 **文档语言**：[English](README.md) | [中文 (当前)](README.zh-CN.md)  
> 📄 **技术白皮书**：[技术白皮书与 API 指南 (中文)](SPECIFICATION-Curve25519.zh-CN.md) | [Specification Whitepaper (English)](SPECIFICATION-Curve25519.en.md)  
> 🌉 **配套上位机虚拟桥**：[Satochip-25519-Omni-Bridge](https://github.com/chx818/Satochip-25519-Omni-Bridge)  

---

## 项目概述

**`Satochip-25519-Applet`** 是基于官方开源 [Toporin/SatochipApplet](https://github.com/Toporin/SatochipApplet) 深度重构的 JavaCard 智能卡固件分支。项目结合 [`suut/Curve25519-JavaCard`](https://github.com/suut/Curve25519-JavaCard) 硬件扩展库（AID `FF00025519`），专门为 **NXP J3R452 (P71D600)** 芯片注入原生硅芯片硬件加速的 **Ed25519 数字签名**、**X25519 密钥协商**以及 **SLIP-0010 多链子私钥派生**能力。

### 核心架构特性

* **零回归向后兼容（Zero Regression）**：100% 保持原有 `secp256k1` 体系（比特币/以太坊 BIP32 派生、普通与 SegWit 交易、BIP340 Schnorr、Taproot、MuSig2、Liquid）。官方 Electrum-Satochip、Satomask 等客户端无感兼容。
* **双曲线物理内存隔离**：`secp256k1` 与 `Curve25519` 两套密码学状态机在卡内 RAM 中物理隔离。两套体系统一共享卡片唯一的 BIP39 Master Seed、统一 PIN 鉴权状态、统一失败重试计数器与 SecureChannel 加密会话。
* **原生硬件加速**：Ed25519 签名直接调度 NXP 加密硬件协处理器执行，典型耗时仅约 **220 ms**。
* **SLIP-0010 多链硬派生**：支持 Solana (501')、TON (607')、Sui (784')、Aptos (637')、Polkadot (354') 与 Near (397') 等公链。
* **Authentikey 签名公钥导出**：派生指令（`0x6B`）导出的 Montgomery 坐标附带由卡片内部 Authentikey 签发的 ECDSA 签名，上位机在核验卡片真实性的同时完成 Edwards 公钥的双有理坐标反解。
* **强绑定 2FA 交易验证 (WYSIWYS)**：全报文 SHA-256 摘要与 HMAC-SHA1 强绑定，确保大报文分包传输的完整性。

---

> [!NOTE]
> **项目说明**：本项目属于实验性社区开源项目。与原版 SatochipApplet 相同，密钥派生（BIP32 / SLIP-0010）均采用软件 HMAC-SHA512 结合卡内硬件 SHA-512 协处理器执行，而 Curve25519（Ed25519 / X25519）的密码学运算则由 NXP 原生底层加密协处理器提供全硬件加速。

---

## 官方预编译发行产物 (Reproducible Builds)

发行二进制产物经过两次独立环境快照双编译，并通过 Oracle 官方离卡验证器（Off-Card Verifier）逐字节校验：

| Artifact | File Path | SHA-256 Hash |
| :--- | :--- | :--- |
| **JavaCard CAP** | [`dist/SatoChip-J3R452-Curve25519.cap`](dist/SatoChip-J3R452-Curve25519.cap) | `9fb7394addd25dbf02d91f805aee04d106a9daa00d3e8df5dca4b6250a8b1dc4` |
| **哈希清单** | [`dist/SHA256SUMS`](dist/SHA256SUMS) | 产物完整哈希签名 |
| **构建审计** | [`dist/build-manifest.json`](dist/build-manifest.json) | 编译环境、依赖组件与重现记录清单 |

---

## 极速上手：卡片一键部署

### 前置准备
* 一张 NXP JCOP 4.5 / J3R452 (P71D600) 智能卡（接触式或非接触式 NFC 卡均可）。
* 任意标准的 PC/SC 智能卡读卡器。
* 系统环境具备 Python 3.8+ 或 Java 17+（仓库已内置 GlobalPlatformPro `gp.jar` 与 `gp.exe`）。

### 一键部署命令

```powershell
# Windows PowerShell:
.\install.ps1

# 若已有旧版 Satochip 需要清除后覆盖安装：
.\install.ps1 --replace
```

```cmd
:: Windows CMD:
install.bat
```

部署脚本会自动探测卡片的 GlobalPlatform 注册表。若卡片尚未安装 `Curve25519` 底层支持库（AID `FF00025519`），会自动优先安装 `lib/Curve25519.cap`，随后安装 `Satochip-25519-Applet`（AID `5361746F4368697000`）。

---

## 源码编译与确定性验证 (Deterministic Build)

### 编译依赖
* **JDK 17 或更高版本**，并配置 `JAVA_HOME`。
* 递归拉取 Git 子模块（包含 Oracle JavaCard SDKs）：
  ```bash
  git submodule update --init --recursive
  ```

### 编译命令

```powershell
# 运行确定性双构建编译与离卡验证：
.\build.ps1

# 或直接通过 Gradle Wrapper 编译：
./gradlew convertJavacard
```

编译产物 CAP 将自动与官方校验和 `9fb7394addd25dbf02d91f805aee04d106a9daa00d3e8df5dca4b6250a8b1dc4` 比对，保证逐字节一致。

---

## 扩展 APDU 指令速查

所有 Satochip 指令均使用 `CLA = 0xB0`，要求在已建立的 **SecureChannel (AES-128-CBC + HMAC-SHA1)** 加密通道中传输。

| INS | 指令名称 | P1 | P2 | 数据字段 (Lc) | 返回数据 (Le) | 说明 |
| :---: | :--- | :---: | :---: | :--- | :--- | :--- |
| **`0x3C`** | `INS_GET_STATUS` | `0x00` | `0x00` | 无 | 19 字节 | 状态报文第 18 字节为 `0x00` 表示 Ed25519 硬件加速引擎就绪 |
| **`0x6B`** | `INS_SLIP10_GET_EXTENDED_KEY` | depth (1..10) | `0x00` / `0x01` / `0x02` | `P2=0/2`: path<br>`P2=1`: path + pubkey | chaincode + public_val + Authentikey 签名 | 执行 SLIP-0010 硬派生并暂存密钥（`P2=0x02` 导出 Montgomery 坐标） |
| **`0x70`** | `INS_SIGN_ED25519_MESSAGE` | `0xFF` | `0x00` | `[msg_bytes (1..149B)]` | `[sig(64B)]` | 硬件协处理器执行 Ed25519 签名并进行成对核验 |
| **`0x68`** | `INS_X25519_KEY_AGREEMENT` | `0xFF` | `0x00` | `[remote_u(32B)]` | `[shared_secret(32B)]` | 执行 RFC 7748 硬件密钥协商，自动规约别名点与拒绝弱点 |

完整协议报文细节、时序图与状态字，请参考 [技术白皮书与 API 指南](SPECIFICATION-Curve25519.zh-CN.md)。

---

## 生态配套工具与驱动

如果要将你的硬件卡片无缝接入 Web3 浏览器钱包（**Phantom、Solflare、Tonkeeper、Sui Wallet、Petra、Polkadot.js**），请配合我们的上位机驱动使用：

👉 **[Satochip-25519-Omni-Bridge](https://github.com/chx818/Satochip-25519-Omni-Bridge)**：Windows 内核免驱虚拟 Ledger Nano S 桥接器，支持全链自动路由与硬件级签名。

---

## 开源许可证

本项目基于 **GNU Lesser General Public License v3.0 (LGPL-3.0)** 许可证开源。详情请参阅 [`LICENSE`](LICENSE)。  
原版 SatochipApplet 版权归属 Toporin 与 Satochip S.R.L. 所有。
