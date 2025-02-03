# 目录/MENU
- [中文部分](#Freak嵌入式-MicroPython开源仓库)
- [English Section](#FreakStudio-MicroPython-Open-Source-Repository)

# Freak嵌入式-MicroPython开源仓库

## Freak嵌入式工作室介绍👨‍💻🌟

Freak嵌入式工作室位以嵌入式电子套件及相关教程、成品电子模块开发、个人DIY电子作品为主要产品，致力于嵌入式教育📚和大学生创新创业比赛、电子计算机类比赛培训🧑‍💻。

**我们希望为电子DIY爱好者提供全面系统的教程和有趣的电子模块，帮助其快速完成项目相关知识学习和产品原型设计!**

💡如有任何问题或需要帮助，请通过邮件📧： 10696531183@qq.com 联系 **李清水 / Freak** 。
![FreakStudio_Contact](image/FreakStudio_Contact.png)
更多信息可在个人主页查看：  
[leezisheng](https://github.com/leezisheng/leezisheng)

## 开源仓库介绍

### serial-servo
[**serial_servo**](https://github.com/leezisheng/freakstudio-micropython-libraries/tree/main/serial_servo)
该模块展示了如何使用MicroPython控制串口舵机扩展板（FreakStudio-多米诺系列扩展板），通过串口通信，用户可以控制多个舵机的角度、速度等参数，实现高效、灵活的舵机控制。
程序中使用了串口通讯与舵机进行数据交互，提供了完整的控制命令和反馈解析功能。

主要特性包括：
- 使用UART串口与舵机通信，支持多舵机控制。
- 支持舵机的角度、速度、工作模式等多种设置。
- 支持舵机温度、电压、角度等实时读取。
- 校验和机制确保数据传输的完整性，幻尔科技串口舵机28条指令全部实现，并且封装为类。
- 完整的异常捕获机制，对入口参数进行详细检查。
- 注释完善，所有方法和类均提供了类型注解。

该软件必须在提供的串口舵机扩展板（FreakStudio-多米诺系列扩展板）上运行，才能确保其正常工作。请参阅硬件开源链接和商品链接获取详细信息。
- **商品链接**：[串口舵机扩展板购买链接]
- **硬件开源链接**：[硬件开源资料链接]

# FreakStudio-MicroPython-Open-Source-Repository

Freak Embedded Studio focuses on embedded electronic kits, related tutorials, finished electronic module development, and personal DIY electronic projects. We are committed to embedded education 📚 and training for university students in innovation and entrepreneurship competitions, as well as electronic and computer-related competitions 🧑‍💻.

**We aim to provide comprehensive tutorials and interesting electronic modules for DIY electronics enthusiasts, helping them quickly learn project-related knowledge and design product prototypes!**

💡 If you have any questions or need assistance, please contact **Li Qingshui / Freak** via email 📧: 10696531183@qq.com.
![FreakStudio_Contact](image/FreakStudio_Contact.png)
For more information, visit my personal homepage:  
[leezisheng](https://github.com/leezisheng/leezisheng)

## Open Source Repository Introduction

### serial-servo
[**serial_servo**](https://github.com/leezisheng/freakstudio-micropython-libraries/tree/main/serial_servo)
This module demonstrates how to control a serial servo expansion board (FreakStudio - Domino series expansion board) using MicroPython. Through serial communication, users can control parameters such as the angle and speed of multiple servos, achieving efficient and flexible servo control.  
The program uses serial communication to interact with the servos and provides complete control commands and feedback parsing functionality.

Key features include:  
- UART serial communication with servos, supporting multi-servo control.  
- Supports settings such as servo angle, speed, and working mode.  
- Real-time reading of servo parameters like temperature, voltage, and angle.  
- A checksum mechanism ensures data transmission integrity. All 28 control commands of the Huaner Technology serial servos are implemented and encapsulated in a class.  
- A complete exception handling mechanism with detailed checks for input parameters.  
- Comprehensive comments with type annotations for all methods and classes.  

This software must run on the provided serial servo expansion board (FreakStudio - Domino series expansion board) to function correctly. Please refer to the hardware open source link and product link for more details.  
- **Product Link**: [Serial Servo Expansion Board Purchase Link]  
- **Hardware Open Source Link**: [Hardware Open Source Information Link]