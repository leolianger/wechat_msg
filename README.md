# 微信提醒功能
### 需要微信企业号
* 企业号可以随意注册，只需要管理员手机短信和微信认证。注册链接：https://work.weixin.qq.com/wework_admin/register_wx
* 在cfg.json中填写corp_id和secret
* 不分组，给所有关注的人发送
### 发送格式：
<font color=red>http://xxx/send?sendkey={sendkey}&text={text}</font><font color=gray>&desp={desp}</font>
* sendkey：应用id
* text：标题
* desp：描述（支持markdown语法)
> cfg.json中的base_url是服务器的域名，如果不用域名而是ip的话在微信打开消息链接的时候会有警告提示。
