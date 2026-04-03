from setuptools import setup, find_packages

setup(
    name="pass-reverse",
    version="0.1.0",
    description="PASS(NICE 평가정보) 휴대폰 본인 인증을 역공학한 라이브러리입니다.",
    packages=find_packages(exclude=["examples", "src"]),
    include_package_data=True,
    package_data={
        "pass_reverse.gui": [
            "templates/*.html",
            "templates/**/*.html",
            "static/css/*.css",
            "static/fonts/*.woff2",
            "static/js/*.js",
            "static/js/**/*.js",
        ],
    },
    python_requires=">=3.6",
    install_requires=[
        "flask>=3.1.1",
        "requests>=2.32.5",
        "beautifulsoup4>=4.12.3",
        "urllib3>=1.26.20",
        "cryptography>=42.0.0",
    ],
)
