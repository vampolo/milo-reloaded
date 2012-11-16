function [recomList] = onLineRecom_AsySVD (userProfile, model,param)
%userProfile = vector with ratings of a single user
%model = model created with createModel function 
% model:    model.mu --> average rating
%           model.bu --> vector of the average rating for each user
%           model.bi --> vector of the average rating for each item
%           model.q 
%           model.x
%           model.y
%param.postProcessingFunction = handle of post-processing function (e.g., business-rules)
%param.userToTest
%param.isNewUser = if true the "precomputed" user biases are not used

    try
        mu=model.mu;
        bu=model.bu;
        bi=model.bi;
        bu_precomputed=model.bu_precomputed;
        bi_precomputed=model.bi_precomputed;
        x=model.x;
        y=model.y;
        q=model.q;
        ls=size(x,1);
    catch e
        display e
        error ('missing some model field');
    end   
    isNewUser=false;
    if (nargin>2)
        if(isfield(param,'isNewUser'))
            isNewUser = param.isNewUser;
        end
    end
    if (isfield(param,'userToTest'))
        user=param.userToTest;
    else
        user=1;
        isNewUser=true;
    end
    if (isNewUser)
        tmpUnbiasRatings = userProfile;
        tmpUnbiasRatings(find(tmpUnbiasRatings)) = tmpUnbiasRatings(find(tmpUnbiasRatings)) - mu;
        tmpUnbiasRatings(find(tmpUnbiasRatings)) = tmpUnbiasRatings(find(tmpUnbiasRatings)) - bi(find(tmpUnbiasRatings))';
        try
            tmpbu = sum(tmpUnbiasRatings) / (model.lambdaU+nnz(userProfile));
        catch
            tmpbu = 0;
        end
        precomputedUserBias=tmpbu;
        userBias=precomputedUserBias;
    else
        precomputedUserBias = bu_precomputed(user);
        userBias = bu(user);
    end
    pu=zeros(ls,1);
    ratedItems = find(userProfile);
    numRatedItems = length(ratedItems);
    if (numRatedItems==0) 
       warning('empty user profile!');
    end        
    for i=1:numRatedItems
        item=ratedItems(i);
        pu = pu +  (userProfile(item) - (mu+precomputedUserBias+bi_precomputed(item)))*x(:,item);
        pu = pu +  y(:,item);
    end
    pu = pu / sqrt(numRatedItems);   
    
    recomList = mu + userBias + bi + q'*pu; %r_hat_ui = mu + bu(u) + bi(item) + q(:,item)'*pu; 
        

    
    %if (nargin>=3)
    if(isfield(param,'postProcessingFunction'))
        if(strcmp(class(param.postProcessingFunction),'function_handle'))
            recomList=feval(param.postProcessingFunction,recomList,param);
        end
    end
    
end