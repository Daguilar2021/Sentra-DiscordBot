FROM mcr.microsoft.com/dotnet/sdk:10.0

WORKDIR /workspace/apps/api

COPY apps/api/Api.csproj ./
RUN dotnet restore

COPY apps/api/. ./

ENV ASPNETCORE_ENVIRONMENT=Development \
    ASPNETCORE_URLS=http://0.0.0.0:5000

EXPOSE 5000

CMD ["dotnet", "run", "--urls", "http://0.0.0.0:5000"]
