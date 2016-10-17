---
date: 2016-10-17
title: CryEngine и шейдера
slug: cry-shader
tags:
 - cryengine
 - pain
categories:
 - Cry Engine
menu: main
---

Имя вы не зря даёте,
Я скажут вам наперёд:
Как вы яхту назовёте,
Так она и поплывёт!
© "Приключения капитана Врунгеля"

Cry - плакать, рыдать, заплакать, поплакать, расплакаться
Engine - двигатель, мотор, движок

Небольшая история про шейдера в CryEngine. К сожалению, описанное для CryEngine не является исключением.

<!--more-->

### Часть первая. Туманная.

С начала использования CryEngine у нас была проблема: иногда при запуске редактора на загружаемом уровне было черным черно.

Особенно раздражал тот факт, что вероятность данного события достаточно высока: на некоторых компьтерах она была более 50%.

Проблема доставляла достаточно неудобств, чтобы начать копать в этом направлении. Опыт работы с CryEngine был крайне небольшим HLSLи от того раскопки шли медленно.

Первый раз, когда удалось целеноправленно воспроизвести проблему, первая мысль была добавить еще один источник света: я попросил помощи у дизайнера уровней и он помог мне с этим вопросом, но отображение не изменилось. За то он предложил подёргать ползунок времени суток. Внезапно, ночной уровень был светлым.

Анализ параметров, на которые влияет время суток, позволил выявить, что критичным для воспроизведения проблемы является плотность тумана.

Так же, если при наличии проблемы выключить туман, то сцена отображается нормально.

Подозрение сразу пало на шейдера.

Через многократную модификацию шейдеров, удалось выяснить, что один из параметров входной стуктуры шейдера всегда равен нулю. При этом на стороне C++ параметр был задан. То есть из C++ данные передавались, но в шейдер не попадали.

Несколько часов отладки помогли найти виновный кусок кода:
```
        int nSize     = CHWShader_D3D::s_pCurInstVS->m_nDataSize;
        void* pVSData = CHWShader_D3D::s_pCurInstVS->m_pShaderData;
        if (FAILED(hr = GetDevice().CreateInputLayout(&Decl.m_Declaration[0], Decl.m_Declaration.Num(), pVSData, nSize, &pDeclCache->m_pDeclaration)))
        {
            return hr;
        }
```
Этот фрагмент вызывался один раз на объявление структуры входных параметров (одна структура может использоваться в нескольких шейдерах). Далее полученное от DirectX значение кладётся в кэш. Однако, в метод [`CreateInputLayout`](https://msdn.microsoft.com/ru-ru/library/windows/desktop/ff476512(v=vs.85).aspx) явно передаётся тело шейдера, которое в ключе кэша никак не участвует. Когда в структуре существуют параметры, которые шейдер не использует, DirectX в целях оптимизации может не передавать их в видео память.

Таким образом поведение редактора зависило от того, в каком порядке инициализируются шейдера. Так как этот процесс происходит асинхронно, проблема возникает не со 100% вероятностью.

Внезапно, код необходимый для решения проблемы уже был в CryEngine и включался define-ом `FEATURE_PER_SHADER_INPUT_LAYOUT_CACHE`. Таким образом получился фикс-однострочник (https://github.com/CRYTEK-CRYENGINE/CRYENGINE/pull/31).

После этого пришлось поправить пару шейдеров, которые до этого работали сугубо случайно, но тем не менее это решило проблему.

Особенно поразило, что данная проблема существует с CryEngine 3 и по сей день (CryEngine 5). Причины, по которой она не должна проявлять себя в собранных играх, я не вижу.

### Часть вторая. Пакованная.

Шейдера, как известно, пишутся на некотором C-подобном языке [HLSL](https://ru.wikipedia.org/wiki/HLSL). При этом в видеокарту они попадают уже в скомпилированном виде.

В редакторе и в клиенте для разрабртки шейдера обычно компилируются по мере необходимости, но игрокам отаётся сборка с уже скомпилированными шейдерами.

Используемый нашими коллегами алгоритм компиляции шейдеров при сборке игры выглядел крайне странно. При этом компиляция шейдеров занимала порядка 11 часов, из-за чего потребовалось разобраться в этом процессе и ускорить его.

#### Документация от Amazon

Чтение документации на Amazon от Lumberyard (Amazon купил и переименовал CryEngine), показало следующее:

[Compiling Shaders for Release Builds](http://docs.aws.amazon.com/lumberyard/latest/userguide/asset-pipeline-shader-compilation.html):

> To generate shader .pak files use the following tools:
> 
> * **Shader Compiler** – The shader compiler server generates the ShaderList.txt file that contains the list of all shaders used by the game. This server can run locally or on a remote PC. For more information, see [Remote Shader Compiler](http://docs.aws.amazon.com/lumberyard/latest/userguide/mat-shaders-custom-dev-remote-compiler.html).
> * **ShaderCacheGen.exe** – Used to populate the local shader cache folder with all the shaders contained in the ShaderList.txt file. For more information, see [ShaderCache.pak File Generation](http://docs.aws.amazon.com/lumberyard/latest/userguide/mat-shaders-custom-dev-cache-intro.html#mat-shaders-custom-dev-cache-generation).
> * **BuildShaderPak_DX11.bat** – Batch file used to generate the ShaderCache.pak files. For more information, see [ShaderCache.pak File Generation](http://docs.aws.amazon.com/lumberyard/latest/userguide/mat-shaders-custom-dev-cache-intro.html#mat-shaders-custom-dev-cache-generation).

[Remote Shader Compiler](http://docs.aws.amazon.com/lumberyard/latest/userguide/mat-shaders-custom-dev-remote-compiler.html)

> The remote shader compiler is also used to store all the shader combinations that have been requested by the game so far, per platform. These are used during shader cache generation, when all the requested shaders are packed into .pak files for use by the game.
>
> It is not required to have a central remote shader compile server. You can instead set up the shader compiler locally on a PC.

#### Решение проблемы от CryEngine

Суть сводится к том, что в CryEngine нет механизма для сбора списка шейдоров, необходимых для работы игры.

То есть предлагаемый вариант выглядит следующим образом:
